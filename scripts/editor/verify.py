"""Exercise the real editor, notebook runner, saved outputs, and Python LSP."""
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile
import time
from types import SimpleNamespace

import nbformat
import pynvim


def wait(nvim, predicate, label, timeout=90):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        nvim.eval("1")  # Service Neovim events and remote-plugin messages.
        time.sleep(0.1)
    raise AssertionError(f"Timed out: {label}\n{nvim.command_output('messages')}")


def launch(path):
    started = time.monotonic()
    nvim = pynvim.attach("child", argv=["nvim", "--embed", "--headless", "-u",
                                      "/opt/book-tools/editor/bootstrap.lua", str(path)])
    nvim.eval("1")
    nvim.command("doautocmd User VeryLazy")
    assert "Mason package path not found" not in nvim.command_output("messages")
    return nvim, time.monotonic() - started


def close(nvim):
    try:
        nvim.command("qa!")
    except EOFError:
        pass
    nvim.close()


with tempfile.TemporaryDirectory(prefix="verify-", dir="/workspace/.state/editor") as tmp:
    root = Path(tmp)
    notebook = root / "check.ipynb"
    marker = root / "kernel-finished.txt"
    cells = [
        "import os, sys\nimport numpy as np\nassert sys.prefix == '/usr/local'\n"
        "assert os.environ['HOME'].startswith('/workspace/.state/')\n"
        "assert np.arange(4).sum() == 6\nprint('BOOK_KERNEL_OK')",
        "%matplotlib inline\nimport matplotlib.pyplot as plt\nplt.plot([1, 2], [3, 4]); plt.show()\n"
        f"from pathlib import Path\np = Path({str(marker)!r})\n"
        "p.write_text(str(int(p.read_text()) + 1) if p.exists() else '1')",
    ]
    if os.environ["BOOK_KIND"] == "keras":
        cells.insert(1, "os.environ['KERAS_BACKEND'] = 'tensorflow'\nimport keras\n"
                     "assert keras.layers.Dense(2)(np.ones((1, 3))).shape == (1, 2)")
        if os.environ.get("BOOK_GPU") == "1":
            cells[1] += "\nimport tensorflow as tf\nassert tf.config.list_physical_devices('GPU')\n"
            cells[1] += "assert 'GPU' in tf.matmul(tf.ones((2, 2)), tf.ones((2, 2))).device"
    else:
        device = "cuda" if os.environ.get("BOOK_GPU") == "1" else "cpu"
        cells.insert(1, f"import torch\nx = torch.tensor(3., requires_grad=True, device='{device}')\n"
                     "(x*x).backward()\nassert x.grad.item() == 6")
    nbformat.write(nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(c) for c in cells]), notebook)
    molten_state = root / "molten.json"
    nvim, first_start = launch(notebook)
    try:
        sys.path.insert(0, os.environ["XDG_DATA_HOME"] + "/nvim/lazy/molten-nvim/rplugin/python3")
        from molten.outputbuffer import OutputBuffer, _book_render_control_chars
        from molten.outputchunks import Output, OutputStatus, TextLnOutputChunk, TextOutputChunk

        assert _book_render_control_chars("abc\bX") == "abX"
        assert _book_render_control_chars("first\n\rsecond") == "first\nsecond"
        output = Output(None)
        output.status = OutputStatus.DONE
        output.chunks = [TextOutputChunk("download\n0/2"),
                         TextOutputChunk("\b" * 3 + "\r1/2"),
                         TextOutputChunk("\b" * 3 + "\r2/2\n")]
        renderer = object.__new__(OutputBuffer)
        renderer.output = output
        renderer.options = SimpleNamespace(wrap_output=True, limit_output_chars=1000,
                                           output_show_exec_time=False, image_provider="none")
        renderer.canvas = None
        renderer.nvim = SimpleNamespace(current=SimpleNamespace(window=SimpleNamespace(handle=1)))
        for virtual in (False, True):
            rendered, _ = renderer.build_output_text((0, 0, 80, 24), 1, virtual)
            text = "\n".join(rendered)
            assert "download" in text and "2/2" in text and "0/2" not in text
            assert "\b" not in text and "\r" not in text

        saved = Output(None)
        saved.status = OutputStatus.DONE
        saved.chunks = [TextLnOutputChunk("download\n\n0/2"),
                        TextLnOutputChunk("\b" * 3 + "\r1/2"),
                        TextLnOutputChunk("\b" * 3 + "\r2/2")]
        renderer.output = saved
        rendered, _ = renderer.build_output_text((0, 0, 80, 24), 1, False)
        text = "\n".join(rendered)
        assert "download" in text and "2/2" in text and "0/2" not in text
        assert text.count("/2") == 1 and "\b" not in text and "\r" not in text
        wait(nvim, lambda: nvim.eval("exists(':MoltenInit')") == 2, "Molten commands")
        wait(nvim, lambda: nvim.exec_lua("return vim.b.notebook_kernel_initialized == true"), "notebook initialization")
        assert nvim.eval("g:mapleader") == " "
        assert nvim.eval("g:maplocalleader") == "\\"
        assert nvim.eval("maparg('\\r', 'n')")
        assert nvim.eval("maparg('jj', 'i')") == "<Esc>", nvim.eval("maparg('jj', 'i')")
        for kind in ("config", "data", "state", "cache"):
            assert nvim.eval(f"stdpath('{kind}')").startswith("/workspace/.state/editor/")
        assert nvim.current.buffer.options["buftype"] == "acwrite"
        assert not nvim.current.window.options["spell"]
        nvim.command("split")
        assert not nvim.current.window.options["spell"]
        nvim.command("close")
        before = notebook.read_bytes()
        try:
            nvim.command("noautocmd write")
        except pynvim.api.common.NvimError as error:
            assert "E676" in str(error), error
        else:
            raise AssertionError("a notebook save bypassed the converter")
        assert notebook.read_bytes() == before
        assert nvim.eval("g:molten_virt_text_max_lines") == 8
        assert nvim.eval("g:molten_output_win_max_height") == 12

        def executions_done(after=0):
            nvim.eval("MoltenTick()")
            kernels = nvim.eval("MoltenRunningKernels()")
            if not kernels:
                return False
            nvim.command(f"silent MoltenSave {nvim.call('fnameescape', str(molten_state))} {kernels[0]}")
            outputs = json.loads(molten_state.read_text())["cells"]
            return (len(outputs) == len(cells)
                    and all(cell["status"] == 2 and (cell["execution_count"] or 0) > after
                            for cell in outputs))

        def kernel_finished(expected):
            nvim.eval("MoltenTick()")
            return marker.exists() and marker.read_text() == str(expected)

        nvim.exec_lua("vim.fn.maparg(vim.g.maplocalleader .. 'R', 'n', false, true).callback()")

        def saved_outputs():
            stamps = nvim.exec_lua("return {vim.b.mtime, vim.uv.fs_stat(vim.api.nvim_buf_get_name(0)).mtime}")
            assert stamps[0]["sec"] == stamps[1]["sec"], (stamps, nvim.exec_lua("return vim.api.nvim_get_autocmds({event='BufWritePost'})"))
            nvim.command("write")
            result = nbformat.read(notebook, as_version=4)
            errors = [o for c in result.cells for o in c.get("outputs", []) if o.output_type == "error"]
            assert not errors, errors
            return (all(c.execution_count is not None for c in result.cells)
                    and any("image/png" in o.get("data", {}) for c in result.cells for o in c.outputs))

        wait(nvim, lambda: kernel_finished(1), "kernel cell execution")
        wait(nvim, executions_done, "cell output collection")
        assert saved_outputs()
        # Cross a timestamp boundary: output export must not trigger a false
        # external-edit prompt on the next save.
        time.sleep(1.1)
        nvim.command("write")
        time.sleep(1.1)
        assert saved_outputs()
        assert [c.source for c in nbformat.read(notebook, as_version=4).cells] == cells
        # Edit source and execute it before saving: outputs must match the new code.
        for i, line in enumerate(nvim.current.buffer[:]):
            if "BOOK_KERNEL_OK" in line:
                nvim.current.buffer[i] = line.replace("BOOK_KERNEL_OK", "BOOK_EDITED_OK")
        nvim.command("doautocmd TextChanged")
        nvim.exec_lua("vim.treesitter.get_parser(0):parse()")
        nvim.exec_lua("vim.fn.maparg(vim.g.maplocalleader .. 'R', 'n', false, true).callback()")
        wait(nvim, lambda: kernel_finished(2), "edited kernel cell execution")
        wait(nvim, lambda: executions_done(len(cells)), "edited cell output collection")
        assert saved_outputs()
        wait(nvim, lambda: nvim.exec_lua("return #vim.lsp.get_clients({name='pyright'}) > 0"), "notebook Python language server")
        assert "BOOK_EDITED_OK" in notebook.read_text()
        assert "BOOK_KERNEL_OK" not in notebook.read_text()
    except Exception:
        print(nvim.command_output("messages"))
        print(nvim.eval("MoltenRunningKernels()"))
        print("kernel completion:", marker.read_text() if marker.exists() else "missing")
        state = json.loads(molten_state.read_text()) if molten_state.exists() else {"cells": []}
        print("Molten state:", [(cell["execution_count"], cell["status"], cell["success"])
                                for cell in state["cells"]])
        print([(c.execution_count, c.source[:100]) for c in nbformat.read(notebook, as_version=4).cells])
        raise
    finally:
        close(nvim)

    # Reopening must preserve cell source and saved rich output.
    nvim, reopen_start = launch(notebook)
    try:
        wait(nvim, lambda: nvim.exec_lua("return vim.b.notebook_kernel_initialized == true"), "reopen")
        nvim.command("write")
        assert "BOOK_EDITED_OK" in notebook.read_text()
        assert "image/png" in notebook.read_text()
    finally:
        close(nvim)

    script = root / "check.py"
    script.write_text("import numpy as np\nvalue: int = 'wrong'\nprint(np.arange(3))\n")
    nvim, script_start = launch(script)
    try:
        wait(nvim, lambda: nvim.exec_lua("return #vim.lsp.get_clients({name='pyright', bufnr=0}) > 0"), "script Python language server")
        wait(nvim, lambda: any(d.get("source") == "Pyright" for d in nvim.exec_lua("return vim.diagnostic.get(0)")), "Python type diagnostics")
        diagnostics = nvim.exec_lua("return vim.diagnostic.get(0)")
        assert any("int" in d["message"] for d in diagnostics), diagnostics
        assert not any("could not be resolved" in d["message"] for d in diagnostics), diagnostics
        settings = nvim.exec_lua("return vim.lsp.get_clients({name='pyright', bufnr=0})[1].settings")
        assert settings["python"]["pythonPath"] == "/usr/local/bin/python", settings
        completion = nvim.exec_lua("""
          local client = vim.lsp.get_clients({name='pyright', bufnr=0})[1]
          local result = client:request_sync('textDocument/completion', {
            textDocument = {uri=vim.uri_from_bufnr(0)}, position={line=2, character=9}
          }, 10000, 0)
          return result and result.result
        """)
        assert completion and any(item["label"] == "arange" for item in completion["items"]), completion
        nvim.command("silent !python %:S")
        assert nvim.eval("v:shell_error") == 0
    finally:
        close(nvim)

    fresh = root / "new.ipynb"
    nvim, _ = launch(fresh)
    try:
        lines = nvim.current.buffer[:]
        first = next(i for i, line in enumerate(lines) if line.startswith("```python"))
        nvim.current.buffer[first + 1:first + 1] = ["assert 6 * 7 == 42", "print(42)"]
        nvim.command("write")
        nvim.current.window.cursor = (first + 2, 0)
        nvim.command("doautocmd TextChanged")
        assert nvim.exec_lua("return require('otter.keeper').get_current_language_context()") == "python"
        nvim.exec_lua("vim.fn.maparg(vim.g.maplocalleader .. 'r', 'n', false, true).callback()")
        state = root / "new-molten.json"

        def new_output():
            nvim.eval("MoltenTick()")
            kernels = nvim.eval("MoltenRunningKernels()")
            if not kernels:
                return False
            nvim.command(f"silent MoltenSave {nvim.call('fnameescape', str(state))} {kernels[0]}")
            outputs = json.loads(state.read_text())["cells"]
            return len(outputs) == 1 and outputs[0]["status"] == 2

        wait(nvim, new_output, "new notebook cell execution")
        nvim.command("write")
        assert any("42" in o.get("text", "") or "42" in o.get("data", {}).get("text/plain", "")
                   for c in nbformat.read(fresh, as_version=4).cells for o in c.get("outputs", []))
    finally:
        close(nvim)
    print(json.dumps({"book": os.environ["BOOK_KIND"], "gpu": os.environ.get("BOOK_GPU") == "1", "passed": ["existing keybindings", "book-local editor state",
          "notebook execution", "model operation", "plot output", "save and reopen", "notebook and script LSP", "diagnostics", "completion", "new notebook"],
          "headless_launch_seconds": [round(t, 3) for t in (first_start, reopen_start, script_start)],
          "median_headless_launch_seconds": round(statistics.median([first_start, reopen_start, script_start]), 3)}))

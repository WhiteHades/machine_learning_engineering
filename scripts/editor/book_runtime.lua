local function replace_once(source, old, new, path)
  local first = source:find(old, 1, true)
  if not first or source:find(old, first + #old, true) then
    error("unexpected Molten source in " .. path)
  end
  return source:sub(1, first - 1) .. new .. source:sub(first + #old)
end

local function patch_molten_output()
  local path = vim.fn.stdpath("data")
    .. "/lazy/molten-nvim/rplugin/python3/molten/outputbuffer.py"
  local source = table.concat(vim.fn.readfile(path), "\n")
  if source:find("# book editor control rendering", 1, true) then return end

  source = replace_once(source, "from molten.utils import notify_error\n\n", [=[from molten.utils import notify_error


# book editor control rendering
def _book_render_control_chars(text: str) -> str:
    if "\b" not in text and "\r" not in text:
        return text

    lines = [[]]
    column = 0
    for char in text:
        if char == "\n":
            lines.append([])
            column = 0
        elif char == "\r":
            column = 0
        elif char == "\b":
            column = max(0, column - 1)
        else:
            line = lines[-1]
            if column < len(line):
                line[column] = char
            else:
                line.append(char)
            column += 1

    return "\n".join("".join(line) for line in lines)

]=], path)
  source = replace_once(source,
    "            limit = self.options.limit_output_chars\n",
    "            lines_str = _book_render_control_chars(lines_str)\n\n"
      .. "            limit = self.options.limit_output_chars\n", path)
  vim.fn.writefile(vim.split(source, "\n", { plain = true }), path)
end

patch_molten_output()

-- No keybindings: those come from the learner's configuration snapshot.
return {
  -- Molten exports outputs on BufWritePost, so conversion must finish first.
  { "goerz/jupytext.nvim", opts = { async_write = false } },
  { "neovim/nvim-lspconfig", opts = function(_, opts)
    -- This workflow supplies Python tooling, not every workstation language server.
    for name, server in pairs(opts.servers) do
      if name ~= "*" then
        opts.servers[name] = vim.tbl_deep_extend("force", type(server) == "table" and server or {},
          { mason = false, enabled = name == "pyright" or name == "ruff" })
      end
    end
    opts.servers.pyright.settings = vim.tbl_deep_extend("force", opts.servers.pyright.settings or {},
      { python = { pythonPath = "/usr/local/bin/python" } })
  end },
  { "mason-org/mason.nvim", opts = function(_, opts) opts.ensure_installed = {} end },
  { "saghen/blink.cmp", opts = { fuzzy = { implementation = "lua" } } },
}

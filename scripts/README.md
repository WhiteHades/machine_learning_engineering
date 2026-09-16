# setup and commands

run these from the chosen book folder. docker and mise must be available.

## setup once

```sh
mise trust
mise run setup
mise run editor:setup
```

setup downloads the author code and prepares the book's packages. run one setup at a time. docker access may need `sudo -v` or `BOOK_DOCKER=pkexec` before a command.

## practice

```sh
mise run edit -- exercises/chapter02.ipynb
mise run edit -- exercises/work.py
mise run run -- exercises/work.py
mise run lab -- exercises/chapter02.ipynb
mise run notebook -- exercises/chapter02.ipynb
mise run test -- exercises
```

`edit` opens the existing lazyvim setup inside the book environment. `lab` opens jupyter through the printed url. `notebook` runs an existing notebook and saves a copy in `.state/notebooks/`. scripts run from their own folder; keep needed data and helpers beside them.

## notebook keys

press `Esc` for normal mode. `i` enters insert mode for typing. in normal mode, `o` starts a new line below the cursor. each fenced `python` block is a separate cell:

````markdown
```python
print(2 + 3)
```
````

in normal mode, `\r` runs the current cell, `\R` runs all cells, `\a` runs the current and earlier cells, and `\o` shows output. `\i` initializes or reinitializes the kernel. type `:w` then press `Enter` to save. for a python script, save and use `:!python %:S`.

open one notebook per session. rerun earlier cells after reopening to restore variables. plots need a terminal with kitty graphics support. editor setup copies the current config and keys into `.state/editor/`; later system changes are not copied automatically.

## gpu and cpu

tasks use the nvidia gpu when a small calculation passes before launch, with cpu fallback otherwise. `BOOK_GPU=0` forces cpu; `BOOK_GPU=1` requires gpu. errors during the actual task do not rerun it automatically.

the gpu has 4 gb memory. use small batches and models. numpy and scikit learn usually run on cpu. tensorflow and jax use gpu for supported operations. pytorch needs model and data on the same device:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
inputs = inputs.to(device)
targets = targets.to(device)
```

## other commands

`mise run doctor` checks setup. `mise run verify`, `mise run gpu:verify`, and `mise run editor:verify` check the environment, gpu, and editor. `mise run fetch` gets the pinned author code; `mise run shell` opens the book environment.

use `BOOK_PORT=8890` to change port 8888, `BOOK_CELL_TIMEOUT=3600` to change the 600 second cell limit, or `BOOK_MEMORY=32g` to change the 16 gb ram limit. ram is separate from gpu memory.

## storage and accounts

keep work in `exercises/` and downloads, weights, results, and caches in `.state/`. author code stays in `code/`. `code/` and `.state/` are ignored by git. back up needed results separately. docker stores images outside the book folders.

for account tokens, create `.state/services.env` with permissions `600`. use entries such as `HF_TOKEN=token_value`, without quotes or `export`, then run:

```sh
BOOK_ENV_FILE="$PWD/.state/services.env" mise run shell
```

the prefix also works with the other book commands. keep tokens out of notebooks. the container uses book folders and shared scripts; the normal home, editor, and desktop sockets stay outside it.

## optional model service

run from the repository root:

```sh
docker compose -f compose.ollama.yaml up -d --wait
docker compose -f compose.ollama.yaml exec ollama ollama pull qwen3:0.6b
docker compose -f compose.ollama.yaml down
```

add `-f compose.ollama.gpu.yaml` after the first compose file for gpu use. book commands need `BOOK_NETWORK=ml-book-services` and the service address `http://ollama:11434`. model files stay in the compose volume.

source revisions stay in each `book.env`; package versions stay in `Dockerfile` or `requirements.lock`.

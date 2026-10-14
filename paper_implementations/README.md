# paper implementations

write implementations in `exercises/` by hand.

from this folder:

```sh
uv sync
mkdir -p exercises
nvim exercises/new_blank.ipynb
```

LazyVim uses this folder's `.venv` for the notebook kernel, so no user kernel
registration is needed. for a browser instead, run `uv run jupyter lab`.

start with one claim, a baseline, tiny inputs, and one success measure. record
the source, settings, seed, metric, and difference from the paper.

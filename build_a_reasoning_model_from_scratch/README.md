# build a reasoning model from scratch

[official book page](https://www.manning.com/books/build-a-reasoning-model-from-scratch)

[source repository](https://github.com/rasbt/reasoning-from-scratch)

the pinned source is in `code/`. work stays in `exercises/`.

## start

from this folder:

```sh
uv sync  # downloads several GB on first use
mkdir -p exercises
nvim exercises/new_blank.ipynb
```

write the notebook and any helper files by hand. use `code/` as a reference,
not as a source to copy into `exercises/`. LazyVim uses this folder's `.venv`
for the notebook kernel, so no user kernel registration is needed.

for a browser instead, run `uv run jupyter lab` from this folder.

the reference notebooks for chapters 2 to 8 use the `chNN_main.ipynb`
filenames. the book starts with a pretrained qwen3 0.6b model.

the gtx 1650 ti has no native bfloat16 support. use float32 on cpu and
float16 on gpu.

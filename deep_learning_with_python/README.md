# deep learning with python

[official book page](https://www.manning.com/books/deep-learning-with-python-third-edition)

source notebooks are in `code/`. work stays in `exercises/`.

## start

from this folder:

```sh
uv sync  # downloads several GB on first use
mkdir -p exercises
nvim exercises/new_blank.ipynb
```

write the notebook by hand. use `code/` as a reference, not as a source to
copy into `exercises/`. LazyVim uses this folder's `.venv` for the notebook
kernel, so no user kernel registration is needed.

for a browser instead, run `uv run jupyter lab` from this folder.

chapter 2 uses tensorflow. later notebooks use jax by default. set
`KERAS_BACKEND` to `tensorflow` before importing keras to change the backend.

chapters 8 and 9 need kaggle access. chapter 10 needs a local file path in
place of its colab upload cell. chapter 12 needs the large coco files. chapter
16 gemma models need account access and more than 4 gb for the larger model.
chapter 18 needs hardware for tpu, multi gpu, or float 8 work.

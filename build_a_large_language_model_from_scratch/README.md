# build a large language model from scratch

[official book page](https://www.manning.com/books/build-a-large-language-model-from-scratch)

[source repository](https://github.com/rasbt/LLMs-from-scratch)

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

chapters 5 to 7 and appendix e download gpt 2 files. the 124m model needs
about 498 mb for its data file. the sms spam data serves chapter 6 and
appendix e.

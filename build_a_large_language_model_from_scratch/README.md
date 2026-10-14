# build a large language model from scratch

[official book page](https://www.manning.com/books/build-a-large-language-model-from-scratch)

[source repository](https://github.com/rasbt/LLMs-from-scratch)

the pinned source is in `code/`. work stays in `exercises/`.

## start

from this folder:

```sh
uv venv && uv pip install -r requirements.in
mkdir -p exercises/ch02
cp -an code/ch02/01_main-chapter-code/. exercises/ch02/
uv run jupyter lab exercises/ch02/ch02.ipynb
```

keep each chapter's helper files beside its notebook. chapters 2 to 7 and
appendices a to e use this layout.

chapters 5 to 7 and appendix e download gpt 2 files. the 124m model needs
about 498 mb for its data file. the sms spam data serves chapter 6 and
appendix e.

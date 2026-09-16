# build a large language model from scratch

[official book page](https://www.manning.com/books/build-a-large-language-model-from-scratch)

[source repository](https://github.com/rasbt/LLMs-from-scratch)

the pinned source is in `code/`. work stays in `exercises/`. shared setup,
editor, gpu, accounts, and services are in the [shared guide](../scripts/README.md).

## start

from this folder:

```sh
mise trust
mise run setup
mise run editor:setup
mkdir -p exercises/ch02
cp -an code/ch02/01_main-chapter-code/. exercises/ch02/
mise run edit -- exercises/ch02/ch02.ipynb
```

keep each chapter's helper files beside its notebook. chapters 2 to 7 and
appendices a to e use this layout.

chapters 5 to 7 and appendix e download gpt 2 files. the 124m model needs
about 498 mb for its data file. instruction tuning fits the 4 gb gpu with
small batches and short contexts. the sms spam data serves chapter 6 and
appendix e.

chapter 7 can use ollama. start it through the shared guide, set
`BOOK_NETWORK=ml-book-services`, and use
`http://ollama:11434/api/chat`. the `llama3` model needs about 4.7 gb of disk
and about 16 gb of ram.

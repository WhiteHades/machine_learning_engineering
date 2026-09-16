# paper implementations

write implementations in `exercises/` and keep results in `.state/`. shared
setup, gpu selection, accounts, and services are in the [shared guide](../scripts/README.md).

from this folder:

```sh
mkdir -p exercises/my_paper
bash ../scripts/book-container.sh run local/ml-llm:2026-09 \
  python exercises/my_paper/train.py
```

start with one claim, a baseline, tiny inputs, and one success measure. record
the source, settings, seed, metric, and difference from the paper.

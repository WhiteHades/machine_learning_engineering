# hands on machine learning with scikit learn and pytorch

[official source](https://github.com/ageron/handson-mlp)

the pinned source is in `code/`. work stays in `exercises/`. shared setup,
editor, gpu, accounts, and services are in the [shared guide](../scripts/README.md).

## start

from this folder:

```sh
mise trust
mise run setup
mise run editor:setup
cp -an code/10_neural_nets_with_pytorch.ipynb exercises/
mise run edit -- exercises/10_neural_nets_with_pytorch.ipynb
```

daily work usually needs only:

```sh
mise run edit -- exercises/work.py
mise run run -- exercises/work.py
mise run test -- exercises
```

chapters 1 to 19 and appendices a to e follow the filenames in `code/`.
chapter 17 points to an outside resource. chapters 14 to 19 contain solution
sections still marked as work in progress.

appendix e needs its optional image:

```sh
mise run setup:appendix-e
cp -an code/Appendix_E_state_space_models.ipynb exercises/
BOOK_GPU=1 BOOK_IMAGE_OVERRIDE=local/ml-foundation:2026-09-appendix-e \
  mise run lab -- exercises/Appendix_E_state_space_models.ipynb
```

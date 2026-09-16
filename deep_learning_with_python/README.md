# deep learning with python

[official book page](https://www.manning.com/books/deep-learning-with-python-third-edition)

source notebooks are in `code/`. work stays in `exercises/`. shared setup,
editor, gpu, accounts, and services are in the [shared guide](../scripts/README.md).

## start

from this folder:

```sh
mise trust
mise run setup
mise run editor:setup
mise run edit -- exercises/chapter02.ipynb
```

## writing a notebook

`chapter02.ipynb` holds chapter 2 practice. choose a name for each chapter unless the book specifies one. the editor shows code cells as fenced `python` blocks while saving a real notebook file.

press `Esc` for normal mode. move inside a python block, then press `i` for insert mode and type the code. to add another cell, press `Esc`, move to the closing three backticks, press `o`, and type a new block below:

````markdown
```python
x = 5
print(x)
```

```python
print(x * 2)
```
````

press `Esc` before running shortcuts. `\r` runs the cell under the cursor; `\R` runs all cells. type `:w` and press `Enter` to save code and completed outputs. `:wq` saves and closes.

keep one cell per example and run cells in order. the second cell above needs the first cell to define `x`. after reopening, rerun earlier cells to restore variables. type code only, not the book's printed results. notes can go outside the python blocks.

## chapter notes

chapter 2 can also open from the source checkout with:

```sh
mise run lab -- 2
```

chapter 2 uses tensorflow. later notebooks use jax by default. select another
keras backend before importing keras:

```python
import os
os.environ["KERAS_BACKEND"] = "tensorflow"
import keras
```

chapters 8 and 9 need kaggle access. chapter 10 needs a container path in
place of its colab upload cell. chapter 12 needs the large coco files. chapter
16 gemma models need account access and more than 4 gb for the larger model.
chapter 18 needs hardware for tpu, multi gpu, or float 8 work.

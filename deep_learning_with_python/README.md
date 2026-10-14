# deep learning with python

[official book page](https://www.manning.com/books/deep-learning-with-python-third-edition)

source notebooks are in `code/`. work stays in `exercises/`.

## start

from this folder:

```sh
uv venv && uv pip install -r requirements.in
uv run jupyter lab exercises/chapter02.ipynb
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

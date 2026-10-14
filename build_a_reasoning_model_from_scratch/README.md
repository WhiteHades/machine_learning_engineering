# build a reasoning model from scratch

[official book page](https://www.manning.com/books/build-a-reasoning-model-from-scratch)

[source repository](https://github.com/rasbt/reasoning-from-scratch)

the pinned source is in `code/`. work stays in `exercises/`.

## start

from this folder:

```sh
uv venv && uv pip install -r requirements.in
mkdir -p exercises/ch02
cp -an code/ch02/01_main-chapter-code/. exercises/ch02/
uv run jupyter lab exercises/ch02/ch02_main.ipynb
```

chapters 2 to 8 use the same `chNN_main.ipynb` layout. the book starts with a
pretrained qwen3 0.6b model.

the gtx 1650 ti has no native bfloat16 support. use float32 on cpu and
float16 on gpu:

```python
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
cfg = dict(QWEN_CONFIG_06_B)
cfg["dtype"] = torch.float16 if device.type == "cuda" else torch.float32
model = Qwen3Model(cfg).to(device)
```

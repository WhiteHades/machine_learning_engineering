# build a reasoning model from scratch

[official book page](https://www.manning.com/books/build-a-reasoning-model-from-scratch)

[source repository](https://github.com/rasbt/reasoning-from-scratch)

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
mise run edit -- exercises/ch02/ch02_main.ipynb
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

full grpo needs about 43 to 45 gb of gpu memory. chapter 8 distillation needs
about 15 gb before headroom. use small checks on the 4 gb card and save
checkpoints during long runs.

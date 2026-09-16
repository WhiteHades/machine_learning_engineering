"""Small environment checks. These do not implement or grade learner exercises."""

import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import torch


def check_optimizer(device):
    torch.manual_seed(42)
    model = torch.nn.Linear(2, 1).to(device)
    x = torch.ones(8, 2, device=device)
    y = torch.ones(8, 1, device=device)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.05)
    initial = torch.nn.functional.mse_loss(model(x), y).item()
    for _ in range(20):
        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(model(x), y)
        loss.backward()
        optimizer.step()
    final = torch.nn.functional.mse_loss(model(x), y).item()
    assert final < initial, (initial, final)
    with tempfile.TemporaryDirectory(dir='/workspace/.state', prefix='verify-') as directory:
        path = Path(directory) / 'checkpoint.pt'
        torch.save(model.state_dict(), path)
        restored = torch.nn.Linear(2, 1).to(device)
        restored.load_state_dict(torch.load(path, map_location=device, weights_only=True))
        torch.testing.assert_close(model(x), restored(x))
    print(f'PyTorch optimization and checkpoint round trip passed on {device}.')


def check_language_model(model, device):
    model = model.to(device)
    tokens = torch.tensor([[1, 2, 3, 4]], device=device)
    logits = model(tokens)
    assert logits.shape == (1, 4, 64), logits.shape
    loss = torch.nn.functional.cross_entropy(logits.flatten(0, 1), tokens.flatten())
    loss.backward()
    assert torch.isfinite(loss)
    grads = [p.grad for p in model.parameters() if p.grad is not None]
    assert grads and all(torch.isfinite(g).all() for g in grads)
    print('Small author model forward and backward passes passed.')


def check_foundation():
    from sklearn.datasets import load_iris
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import train_test_split
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    import gymnasium as gym

    x, y = load_iris(return_X_y=True)
    x_train, x_test, y_train, y_test = train_test_split(x, y, stratify=y, random_state=42)
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=200))
    model.fit(x_train, y_train)
    assert model.score(x_test, y_test) > 0.8
    with gym.make('CartPole-v1') as env:
        env.reset(seed=42)
        observation, *_ = env.step(0)
        assert observation.shape == (4,)
    with gym.make('LunarLander-v3') as env:
        env.reset(seed=42)
        observation, *_ = env.step(0)
        assert observation.shape == (8,)
    for name in ('Box2D', 'torchvision', 'torchaudio', 'transformers', 'datasets', 'peft', 'trl',
                 'diffusers', 'stable_baselines3', 'xgboost', 'optuna', 'ultralytics'):
        importlib.import_module(name)
    print('Scikit-learn held-out prediction, RL environment step, and chapter imports passed.')


def check_llm(device):
    import tiktoken
    from llms_from_scratch.ch04 import GPTModel

    tokenizer = tiktoken.get_encoding('gpt2')
    text = 'A small tokenizer check.'
    assert tokenizer.decode(tokenizer.encode(text)) == text
    check_language_model(GPTModel(dict(vocab_size=64, context_length=16, emb_dim=32,
                                      n_heads=4, n_layers=2, drop_rate=0.0, qkv_bias=False)), device)
    subprocess.run([sys.executable, '-c', 'import tensorflow as tf; assert callable(tf.train.load_checkpoint); print("GPT checkpoint reader available.")'], check=True)
    for name in ('llms_from_scratch.ch02', 'llms_from_scratch.ch03', 'llms_from_scratch.ch05',
                 'llms_from_scratch.ch06', 'llms_from_scratch.ch07', 'llms_from_scratch.appendix_e', 'chainlit'):
        importlib.import_module(name)


def check_reasoning(device):
    from reasoning_from_scratch.qwen3 import Qwen3Model

    cfg = dict(vocab_size=64, context_length=32, emb_dim=32, n_heads=4, n_layers=2,
               hidden_dim=64, head_dim=8, qk_norm=True, n_kv_groups=2,
               rope_base=1_000_000.0, dtype=torch.float32)
    check_language_model(Qwen3Model(cfg), device)
    for name in ('reasoning_from_scratch.ch02', 'reasoning_from_scratch.ch03',
                 'reasoning_from_scratch.ch04', 'reasoning_from_scratch.ch05',
                 'reasoning_from_scratch.ch06', 'reasoning_from_scratch.ch07',
                 'reasoning_from_scratch.ch08', 'datasets', 'chainlit'):
        importlib.import_module(name)
    print('Reasoning chapter imports passed. No pretrained weights were downloaded.')


def check_keras():
    for backend in ('jax', 'tensorflow', 'torch'):
        env = dict(os.environ, KERAS_BACKEND=backend, XLA_PYTHON_CLIENT_PREALLOCATE='false',
                   TF_FORCE_GPU_ALLOW_GROWTH='true')
        subprocess.run([sys.executable, '-c', '''
import os, keras, numpy as np
backend = keras.config.backend()
if os.environ.get('BOOK_GPU') == '1':
    if backend == 'jax':
        import jax
        assert any(d.platform == 'gpu' for d in jax.devices())
    elif backend == 'tensorflow':
        import tensorflow as tf
        assert tf.config.list_physical_devices('GPU')
    else:
        import torch
        assert torch.cuda.is_available()
model = keras.Sequential([keras.layers.Input(shape=(2,)), keras.layers.Dense(1)])
model.compile(optimizer='sgd', loss='mse')
loss = model.train_on_batch(np.ones((4, 2), dtype='float32'), np.ones((4, 1), dtype='float32'))
assert np.isfinite(loss)
weight = model.weights[0].value
if os.environ.get('BOOK_GPU') == '1':
    if backend == 'jax':
        assert all(d.platform == 'gpu' for d in weight.devices())
    elif backend == 'tensorflow':
        assert 'GPU' in weight.device
    else:
        assert weight.is_cuda
print(f'Keras training passed with {backend}.')
'''], env=env, check=True)


if __name__ == '__main__':
    kind = os.environ['BOOK_KIND']
    gpu = os.environ.get('BOOK_GPU') == '1'
    if gpu:
        assert torch.cuda.is_available(), 'GPU requested but PyTorch cannot use CUDA.'
        print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    device = torch.device('cuda' if gpu else 'cpu')
    print(f'Checking {kind}: Python {sys.version.split()[0]}, PyTorch {torch.__version__}')
    for module in ('jupyterlab', 'ipykernel', 'nbconvert', 'pytest'):
        importlib.import_module(module)
    check_optimizer(device)
    if kind == 'foundation':
        check_foundation()
    elif kind == 'llm':
        check_llm(device)
    elif kind == 'reasoning':
        check_reasoning(device)
    elif kind == 'keras':
        check_keras()
    else:
        raise ValueError(f'Unknown book: {kind}')
    print('Environment verification passed. Chapter training and learner solutions are separate checks.')

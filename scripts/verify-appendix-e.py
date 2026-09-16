"""Exercise the author's optional CUDA extensions on a small input."""

import torch
from mamba_ssm import Mamba

assert torch.cuda.is_available(), 'Appendix E extension verification requires CUDA.'
model = Mamba(d_model=16, d_state=8, d_conv=4, expand=2).cuda()
x = torch.randn(2, 8, 16, device='cuda', requires_grad=True)
y = model(x)
assert y.shape == x.shape
y.square().mean().backward()
assert torch.isfinite(y).all() and torch.isfinite(x.grad).all()
print('Appendix E Mamba and causal-conv1d forward/backward passes passed on', torch.cuda.get_device_name())

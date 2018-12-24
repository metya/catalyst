import torch
import torch.nn as nn
from collections import OrderedDict
from catalyst.utils.misc import pairwise


class ResidualWrapper(nn.Module):
    def __init__(self, net):
        super().__init__()
        self.net = net

    def forward(self, x):
        return x + self.net(x)


class SequentialNet(nn.Module):
    def __init__(
        self,
        hiddens,
        layer_fn=nn.Linear,
        bias=True,
        norm_fn=None,
        activation_fn=nn.ReLU,
        dropout=None,
        block_parts=None,
        residual=False
    ):
        super().__init__()
        # hack to prevent cycle imports
        from catalyst.modules.modules import name2nn

        layer_fn = name2nn(layer_fn)
        activation_fn = name2nn(activation_fn)
        norm_fn = name2nn(norm_fn)
        dropout = name2nn(dropout)

        block_parts = block_parts or ["layer", "norm", "drop", "activation"]

        if isinstance(dropout, float):
            dropout = lambda : nn.Dropout(dropout)

        def _layer_fn(f_in, f_out, bias):
            return layer_fn(f_in, f_out, bias=bias)

        def _normalize_fn(f_in, f_out, bias):
            return norm_fn(f_out) if norm_fn is not None else None

        def _dropout_fn(f_in, f_out, bias):
            return dropout() if dropout is not None else None

        def _activation_fn(f_in, f_out, bias):
            return activation_fn() if activation_fn is not None else None

        name2fn = {
            "layer": _layer_fn,
            "norm": _normalize_fn,
            "drop": _dropout_fn,
            "activation": _activation_fn,
        }

        net = []

        for i, (f_in, f_out) in enumerate(pairwise(hiddens)):
            block = []
            for key in block_parts:
                fn = name2fn[key](f_in, f_out, bias)
                if fn is not None:
                    block.append((f"{key}", fn))
            block = torch.nn.Sequential(OrderedDict(block))
            if residual:
                block = ResidualWrapper(net=block)
            net.append((f"block_{i}", block))

        self.net = torch.nn.Sequential(OrderedDict(net))

    def forward(self, x):
        x = self.net.forward(x)
        return x

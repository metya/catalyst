import sys
import copy
import random
import collections
import numpy as np
import importlib.util
from itertools import tee


def pairwise(iterable):
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)


def merge_dicts(*dicts):
    """
    Recursive dict merge.
    Instead of updating only top-level keys,
        dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys.
    """
    assert len(dicts) > 1

    dict_ = copy.deepcopy(dicts[0])

    for merge_dict in dicts[1:]:
        for k, v in merge_dict.items():
            if (k in dict_ and isinstance(dict_[k], dict)
                    and isinstance(merge_dict[k], collections.Mapping)):
                dict_[k] = merge_dicts(dict_[k], merge_dict[k])
            else:
                dict_[k] = merge_dict[k]

    return dict_


def set_global_seeds(i):
    try:
        import torch
    except ImportError:
        pass
    else:
        torch.manual_seed(i)
        torch.cuda.manual_seed_all(i)
    try:
        import tensorflow as tf
    except ImportError:
        pass
    else:
        tf.set_random_seed(i)
    random.seed(i)
    np.random.seed(i)


def import_module(name, path):
    spec = importlib.util.spec_from_file_location(
        name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def boolean_flag(parser, name, default=False, help=None):
    """
    Add a boolean flag to argparse parser.

    Parameters
    ----------
    parser: argparse.Parser
        parser to add the flag to
    name: str
        --<name> will enable the flag, while --no-<name> will disable it
    default: bool or None
        default value of the flag
    help: str
        help string for the flag
    """
    dest = name.replace("-", "_")
    parser.add_argument(
        "--" + name, action="store_true",
        default=default, dest=dest, help=help)
    parser.add_argument("--no-" + name, action="store_false", dest=dest)


class FrozenClass(object):
    __isfrozen = False

    def __setattr__(self, key, value):
        if self.__isfrozen and not hasattr(self, key):
            raise TypeError("%r is a frozen class" % self)
        object.__setattr__(self, key, value)

    def _freeze(self):
        self.__isfrozen = True

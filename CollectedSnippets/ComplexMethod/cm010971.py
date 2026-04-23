def apply(x):
        from torch.nn.parallel.scatter_gather import _is_namedtuple

        if isinstance(x, torch.Tensor):
            return fn(x)
        elif hasattr(x, "__dataclass_fields__"):
            dc = dataclasses.replace(x)
            changes = {
                f.name: apply(getattr(dc, f.name)) for f in dataclasses.fields(dc)
            }
            return dataclasses.replace(dc, **changes)
        elif isinstance(x, OrderedDict):
            od = x.__class__()
            for key, value in x.items():
                od[key] = apply(value)
            return od
        elif isinstance(x, PackedSequence):
            apply(x.data)
            return x
        elif isinstance(x, dict):
            return {key: apply(value) for key, value in x.items()}
        elif _is_namedtuple(x):
            res = (apply(el) for el in x)
            return type(x)(*res)
        elif isinstance(x, (list, tuple, set)):
            return type(x)(apply(el) for el in x)
        else:
            return x
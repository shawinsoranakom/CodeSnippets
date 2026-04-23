def __torch_function__(cls, func, types, args=(), kwargs=None):
                kwargs = kwargs or {}
                if func is torch.autograd.backward:
                    backward_called_with_subclass[0] = True
                    # unwrap inner tensors and call the real backward
                    new_args = []
                    for arg in args:
                        if isinstance(arg, tuple):
                            new_args.append(
                                tuple(a._data if isinstance(a, cls) else a for a in arg)
                            )
                        elif isinstance(arg, cls):
                            new_args.append(arg._data)
                        else:
                            new_args.append(arg)
                    return func(*new_args, **kwargs)
                return func(
                    *tuple(a._data if isinstance(a, cls) else a for a in args), **kwargs
                )
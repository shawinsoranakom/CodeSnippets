def wrapper(*args, **kwargs):
                if len(args) > num_positional_params:
                    args, kwargs = remap_deprecated_args(args, kwargs)
                return func(*args, **kwargs)
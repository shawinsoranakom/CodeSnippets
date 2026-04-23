def _get_functional(cls):
        functional_list = []
        for f in dir(torch.nn.functional):
            if not f.islower():
                continue
            # Ignore internal functions
            if f.startswith("_"):
                continue
            # Ignore supporting functions
            if f in cls.IGNORE_FUNCS:
                continue
            fn = getattr(torch.nn.functional, f)
            # Ignore non-callable object like modules
            if not isinstance(fn, Callable):
                continue
            if f not in cls.FUNCTIONALS_WITHOUT_ANNOTATION:
                try:
                    sig = inspect.signature(fn)
                    has_tensor_arg = False
                    for param in sig.parameters.values():
                        if isinstance(param.annotation, type) and issubclass(
                            param.annotation, torch.Tensor
                        ):
                            has_tensor_arg = True
                    if not has_tensor_arg:
                        continue
                # No signature or Object is not supported
                except ValueError:
                    pass
            functional_list.append((f, fn))
        return functional_list
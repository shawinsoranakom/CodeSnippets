def __call__(self, body_fn, args, kwargs, hints):
        r"""
        Call implementation of hints_wrapper

        Args:
            body_fn (Callable): A callable function that is within the scope
             that is being traced.

            args (Tuple of torch.Tensor/int/float/bool): A tuple of inputs to
             body_fn.

            kwargs (dict): Keyword argument to the body_fn.

            hints (dict): A dict of context hints which could be passed to
             backend compiler.
        """
        if not isinstance(args, tuple):
            args = tuple(args)

        if not all(isinstance(t, (torch.Tensor, int, float, bool)) for t in args):
            raise RuntimeError(
                f"args must be a tuple of tensors, ints, floats, or bools, got {args}"
            )

        if not isinstance(kwargs, dict):
            raise RuntimeError(f"kwargs must be a dict, got {type(kwargs)}")

        if len(kwargs) > 0:
            raise RuntimeError(
                f"kwargs except for hints are not supported, got {kwargs}"
            )

        if not isinstance(hints, dict):
            raise RuntimeError(f"hints must be a dict, got {type(hints)}")

        for k, v in hints.items():
            if not isinstance(k, str):
                raise RuntimeError(f"hints key must be a str, got {k}.")

            if not isinstance(v, (int, float, bool, str)):
                raise RuntimeError(
                    "hints must be a dict containing int, float, bool or str "
                    f"value, got value {v} for key {k}."
                )

        # pyrefly: ignore [missing-attribute]
        return super().__call__(body_fn, args, kwargs, hints)
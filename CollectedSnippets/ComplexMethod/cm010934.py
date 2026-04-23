def maybe_fallback(*args: _P.args, **kwargs: _P.kwargs):
            if torch.compiler.is_compiling() and (
                not kwargs.get("capturable", False)
                and has_state_steps
                and (arg := args[state_steps_ind])
                and isinstance(arg, Sequence)
                and arg[0].device.type in {"cuda", "xpu"}
                or (
                    "state_steps" in kwargs
                    and (kwarg := kwargs["state_steps"])
                    and isinstance(kwarg, Sequence)
                    and kwarg[0].device.type in {"cuda", "xpu"}
                )
            ):
                return disabled_func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
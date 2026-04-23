def __torch_function__(
        cls,
        orig_method: Callable[..., Any],
        types: tuple[type, ...],
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> "Proxy":
        args = args if args else ()
        kwargs = kwargs if kwargs else {}

        tracers: dict[TracerBase, None] = {}

        def find_tracer(a: Any) -> None:
            if isinstance(a, cls):
                tracers[a.tracer] = None

        tree_map_(find_tracer, args)
        tree_map_(find_tracer, kwargs)

        if len(tracers) > 1:
            raise RuntimeError(
                f"Found multiple different tracers {list(tracers.keys())} while "
                f"trying to trace operations {orig_method}"
            )
        tracer = next(iter(tracers.keys()))

        if isinstance(orig_method, torch._C.ScriptMethod):
            args = (orig_method.owner,) + args
            return tracer.create_proxy("call_method", orig_method.name, args, kwargs)
        if torch.overrides.is_tensor_method_or_property(orig_method):
            return tracer.create_proxy(
                "call_method", orig_method.__name__, args, kwargs
            )
        else:
            if isinstance(orig_method, torch._ops.HigherOrderOperator):
                bad_callable = _find_arbitrary_callable(args, kwargs)
                if bad_callable is not None:
                    raise RuntimeError(
                        f"Unable to symbolically trace the HigherOrderOperator "
                        f"{orig_method._name} because it received an arbitrary "
                        f"callable argument {bad_callable}. Use make_fx or dynamo "
                        f"tracing instead."
                    )
            return tracer.create_proxy(
                "call_function",
                orig_method,
                args,
                kwargs,
                name=tracer.graph._target_to_str(orig_method.__name__),
            )
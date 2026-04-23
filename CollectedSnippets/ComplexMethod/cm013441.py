def __torch_function__(
        cls,
        orig_method: Callable[..., Any],
        types: tuple[type, ...],
        args: tuple[Any, ...] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> "MetaProxy":
        args = args if args else ()
        kwargs = kwargs if kwargs else {}

        meta_proxy = None
        for arg in args:
            if isinstance(arg, MetaProxy):
                meta_proxy = arg
                break

        if meta_proxy is None:
            raise AssertionError(
                "No MetaProxy found in arguments, but one is expected."
            )

        proxy = super().__torch_function__(orig_method, types, args, kwargs)
        with meta_proxy.fake_mode:
            proxy.node.meta["val"] = orig_method(
                *[a.node.meta["val"] if isinstance(a, Proxy) else a for a in args],
                **kwargs,
            )
        return MetaProxy(proxy.node, proxy.tracer, meta_proxy.fake_mode)
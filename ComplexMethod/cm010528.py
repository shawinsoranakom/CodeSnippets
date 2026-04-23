def __torch_function__(
        self,
        orig_func: Callable[_P, _R],
        types: Sequence[type],
        args: Sequence[Any] = (),
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        if kwargs is None:
            kwargs = {}
        # For primitive operations, run them as is without interception
        # Unless we are in prims_mode, in which case we want to use nvprims
        if orig_func in torch_function_passthrough or orig_func in all_prims():
            with self.prims_mode_cls():
                # pyrefly: ignore [invalid-param-spec]
                return orig_func(*args, **kwargs)
        mapping = torch_to_refs_map()
        func = mapping.get(orig_func, None)

        # For torch.ops.aten.*, use registered decompositions from torch._decomp
        # torch._decomp.decomposition_table provides a mapping from
        # torch.ops.aten.* to torch._refs or torch._decomp.decompositions
        # implementations.
        # There're other ways to implement this functionality,
        # see https://github.com/pytorch/pytorch/pull/82657#discussion_r939776417
        if func is None and isinstance(orig_func, torch._ops.OpOverload):
            func = torch._decomp.decomposition_table.get(orig_func, None)
        elif func is None and isinstance(orig_func, torch._ops.OpOverloadPacket):
            default = getattr(orig_func, "default", None)
            if default is None and orig_func._dir:
                default = getattr(orig_func, orig_func._dir[0], None)
            if default is not None:
                func = torch._decomp.decomposition_table.get(default, None)

        if func is not None:
            # If the ref exists query whether we should use it or not
            if self.should_fallback_fn(self, orig_func, func, args, kwargs):
                # pyrefly: ignore [invalid-param-spec]
                return orig_func(*args, **kwargs)
            # torch calls inside func should be interpreted as refs calls
            with self:
                return func(*args, **kwargs)
        if self.strict:
            raise RuntimeError(
                f"no _refs support for {torch.overrides.resolve_name(orig_func)}"
            )
        # pyrefly: ignore [invalid-param-spec]
        return orig_func(*args, **kwargs)
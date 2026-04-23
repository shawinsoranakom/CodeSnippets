def __torch_dispatch__(
        self,
        func: "OpOverload",
        types: Iterable[type],
        args: tuple[Any, ...] = (),
        kwargs: dict[Any, Any] | None = None,
    ) -> Any:
        kwargs = kwargs or {}

        def maybe_clone(t: torch.Tensor) -> None:
            tid = _get_tid(t)
            sid = _get_sid(t)
            ctx = self.ctx
            if sid in ctx.sid_to_tid:
                for tid in ctx.sid_to_tid[sid]:
                    if tid not in ctx.tid_to_weakhandle:
                        # We know that if tid is in sid_to_tid, then it must also be in
                        # tid_to_weakhandle. However, it is possible for the tensor to be
                        # saved at one point, but cleared by backward before it is modified
                        # in-place. Consider the following example:
                        #
                        # >>> a = torch.randn(2, 3, requires_grad=True).clone()
                        # >>> out = (a**2).sum()
                        # >>> out.backward()
                        # >>> a.sin_()
                        continue
                    handle = ctx.tid_to_weakhandle[tid]
                    if handle in ctx.cloned:
                        # The same exact tensor has been cloned already
                        continue
                    ctx.cloned[handle] = ctx.original[handle].clone()
                    del ctx.original[handle]

        for idx, arg in enumerate(func._schema.arguments):
            if arg.alias_info is not None and arg.alias_info.is_write:
                if arg.is_out:
                    maybe_clone(kwargs["out"])
                elif isinstance(args[idx], list):
                    # Foreach case. (Possible optimization: if most of the
                    # tensors need to be cloned, use a for each clone?)
                    for t in args[idx]:
                        maybe_clone(t)
                else:
                    maybe_clone(args[idx])

        return func(*args, **kwargs)
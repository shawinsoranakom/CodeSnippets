def _get_op_profile(node: torch.fx.Node) -> OpProfile:
        args_profile = tuple(
            TensorMetadata.maybe_from_tensor(arg.meta.get("val"))
            if isinstance(arg, torch.fx.Node)
            else None
            for arg in (*node.args, *node.kwargs.values())
        )

        out_profile = None
        meta = node.meta.get("val")
        if meta is None:
            raise AssertionError("node.meta['val'] must not be None")
        if isinstance(meta, torch.Tensor):
            out_profile = TensorMetadata.maybe_from_tensor(meta)
        elif isinstance(meta, (list, tuple)):
            out_profile = tuple(TensorMetadata.maybe_from_tensor(m) for m in meta)  # type: ignore[assignment]
        if out_profile is None:
            raise AssertionError(
                f"out_profile must not be None for meta type {type(meta)}"
            )

        return OpProfile(args_profile, out_profile)
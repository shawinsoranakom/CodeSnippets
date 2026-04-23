def is_aligned(x: KernelArgType, alignment: int, include_tensor: bool) -> bool:
        """
        Roughly follow triton code here:
        https://github.com/triton-lang/triton/blob/5282ed890d453e10b9ee30076ef89115dd197761/python/triton/runtime/jit.py#L208-L222
        """
        if isinstance(x, TensorArg):
            if include_tensor:
                offset_aligned = V.graph.sizevars.statically_known_multiple_of(
                    x.offset * x.dtype.itemsize,
                    alignment,  # type: ignore[arg-type]
                )
                return offset_aligned and not is_unaligned_buffer(x)
            else:
                return False
        if isinstance(x, SizeArg):
            # TODO(voz): These are kinda redundant, if we can solve out statically_known_multiple_of with
            # _maybe_evaluate_static...
            if x.name.startswith("load_seed_offset"):
                return False
            if x.expr is None:
                return False
            if isinstance(x.expr, (float, bool)):
                return False
            return V.graph.sizevars.statically_known_multiple_of(x.expr, alignment)  # type: ignore[arg-type]
        if isinstance(x, WorkspaceArg):
            # We allocate the workspace ourselves, so it is always aligned
            return True
        if isinstance(x, (TMADescriptorArg, ConstexprArg)):
            return False
        raise NotImplementedError(f"unhandled {type(x)}: {x}")
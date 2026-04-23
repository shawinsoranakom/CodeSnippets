def create(  # type: ignore[override]
        cls,
        x: IRNode,
        dim: int,
        start: int,
        end: int,
        step: int = 1,
        clamp: bool = True,
    ) -> IRNode:
        step = sympy.expand(step)
        assert isinstance(step, Expr) or step > 0, step
        try:
            if start == 0 and end >= 2**63 - 1 and step == 1:
                return x
        except TypeError:
            pass

        new_size = list(x.get_size())

        # NB: Ordinarily we default to clamping.
        # We only don't clamp for split_with_sizes. For split_with_sizes, sizes should be already valid
        # failing in this situation is ok, since invalid sizes could trigger silent errors.
        if clamp:
            start, end = cls.normalize_start_end(x, dim, start, end)

        new_size[dim] = FloorDiv(end - start + (step - 1), step)

        if is_storage_and_layout(x):
            # Fast path
            storage, old_layout = as_storage_and_layout(x)
            new_stride = list(old_layout.stride)
            new_stride[dim] = new_stride[dim] * step
            new_layout = FixedLayout(
                old_layout.device,
                old_layout.dtype,
                new_size,
                new_stride,
                old_layout.offset + old_layout.stride[dim] * start,
                old_layout.is_pinned,
            )
            return ReinterpretView(data=storage, layout=new_layout)

        def reindex(
            index: Sequence[Expr],
        ) -> Sequence[Expr]:
            assert len(index) == len(new_size), f"wrong ndim {index} {new_size}"
            index = list(index)
            index[dim] = index[dim] * step + start
            return index

        # redirect to a generic view
        return SliceView(data=x, size=new_size, reindex=reindex)
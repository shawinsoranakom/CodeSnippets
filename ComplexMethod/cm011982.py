def create(cls, x: IRNode, *, dim: int | None = None) -> IRNode:
        if is_storage_and_layout(x):
            storage, old_layout = as_storage_and_layout(x)
            new_size = []
            new_stride = []
            if dim is not None:
                assert isinstance(dim, int), type(dim)
                assert 0 <= dim and dim < len(old_layout.size)

            for i, (size, stride) in enumerate(zip(old_layout.size, old_layout.stride)):
                if dim is None:
                    # Only append if dim is not squeezed out
                    if not V.graph.sizevars.is_size_one_or_false(size):
                        new_size.append(size)
                        new_stride.append(stride)
                else:
                    if i != dim:
                        new_size.append(size)
                        new_stride.append(stride)
                    else:
                        assert size == 1, "expected squeezed size to be 1"

            new_layout = FixedLayout(
                old_layout.device,
                old_layout.dtype,
                new_size,
                new_stride,
                old_layout.offset,
                old_layout.is_pinned,
            )
            return ReinterpretView(data=storage, layout=new_layout)

        if dim is None:
            return View.create(
                x,
                [
                    s
                    for s in x.get_size()
                    if not V.graph.sizevars.is_size_one_or_false(s)
                ],
            )
        else:
            assert x.get_size()[dim] == 1
            return View.create(x, [s for i, s in enumerate(x.get_size()) if i != dim])
def scatter_reduce_(self, dim: int, index, src, reduce, *, include_self: bool = True):
    assert reduce in (None, "sum", "prod", "mean", "amax", "amin")
    assert (
        len(aten.scatter_reduce_.overloads()) == 1
        and "two" in aten.scatter_reduce_.overloads()
    ), "aten.scatter_reduce_.two is not the unique overload of aten.scatter_reduce_"

    if isinstance(src, Number):
        src = full_like(self, src)

    fallback_result = scatter_fallback(
        aten.scatter_reduce_.two,
        self,
        dim,
        index,
        src,
        reduce=reduce,
        include_self=include_self,
    )

    if fallback_result:
        return fallback_result

    assert isinstance(self, TensorBox)
    assert "int" in str(index.get_dtype())

    ndim = len(self.get_size())
    if ndim == 0:
        self = view(self, [1])

    if isinstance(src, TensorBox) and len(src.get_size()) == 0:
        src = view(src, [1])

    if isinstance(index, TensorBox) and len(index.get_size()) == 0:
        index = view(index, [1])

    if index.get_numel() == 0:
        return self

    dim = _validate_dim(self, dim)

    self.realize()
    index_loader = index.make_loader()
    src_loader = src.make_loader() if isinstance(src, TensorBox) else None

    def output_indexer(idx):
        # self is captured from the end of the function, so it may have 0 dim
        shape = self.get_size()
        ndim = len(shape)
        indirect_idx = list(idx)
        indirect_idx[dim] = ops.indirect_indexing(
            index_loader(idx), 1 if ndim == 0 else shape[dim], wrap_neg=False
        )
        return indirect_idx

    def fn(idx):
        if src_loader:
            return src_loader(idx)
        else:
            # src is a scalar
            # pyrefly: ignore [bad-argument-type]
            return ops.constant(src, self.get_dtype())

    def backend_reduce_str(reduce):
        if reduce == "sum":
            return "atomic_add"
        else:
            # TODO: Need to support more reduction type
            assert reduce is None
            return None

    device = self.get_device()
    assert device is not None

    if not include_self:
        # zero out the corresponding elements first
        zero_out = ir.Scatter(
            device=device,
            dtype=self.get_dtype(),
            inner_fn=lambda index: ops.constant(0, self.get_dtype()),
            ranges=index.get_size(),
            output_indexer=output_indexer,
            scatter_mode=None,
        )
        buffer = ir.ComputedBuffer(
            name=None,
            layout=ir.MutationLayoutSHOULDREMOVE(self),
            data=zero_out,
        )
        buffer.name = V.graph.register_buffer(buffer)
        V.graph.register_operation(buffer)

    # self[index[i][j][k]][j][k] += src[i][j][k]  # if dim == 0
    # self[i][index[i][j][k]][k] += src[i][j][k]  # if dim == 1
    # self[i][j][index[i][j][k]] += src[i][j][k]  # if dim == 2
    scatter = ir.Scatter(
        device=device,
        dtype=self.get_dtype(),
        inner_fn=fn,
        ranges=index.get_size(),
        output_indexer=output_indexer,
        scatter_mode=backend_reduce_str(reduce),
    )
    buffer = ir.ComputedBuffer(
        name=None,
        layout=ir.MutationLayoutSHOULDREMOVE(self),
        data=scatter,
    )
    buffer.name = V.graph.register_buffer(buffer)
    V.graph.register_operation(buffer)

    if ndim == 0:
        self = view(self, [])
    return self
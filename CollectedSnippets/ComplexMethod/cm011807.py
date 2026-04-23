def searchsorted(
    sorted_sequence: TensorBox,
    self: TensorBox,
    *,
    out_int32: bool = False,
    right: bool = False,
    side: str | None = None,
    sorter: TensorBox | None = None,
) -> TensorBox:
    validate_bucketize = lambda tb: V.graph.has_feature(  # noqa: E731
        tb, BackendFeature.BUCKETIZE
    )
    if (
        not validate_bucketize(sorted_sequence)
        or not validate_bucketize(self)
        or (sorter is not None and not validate_bucketize(sorter))
    ):
        return fallback_handler(aten.searchsorted.Tensor, add_to_fallback_set=False)(
            sorted_sequence,
            self,
            out_int32=out_int32,
            right=right,
            side=side,
            sorter=sorter,
        )

    # If side is present, override the value of right if needed.  This assumes that
    # validation of the two options being non-contradictory is already done by the
    # searchsorted meta-function.
    if side is not None and side == "right":
        right = True

    index_dtype = torch.int32 if out_int32 else torch.int64
    values_loader = self.make_loader()

    # The entire sorted_sequence tensor needs to be used by ops.bucketize, so we need to
    # realize it into global memory; or in other words, we can't guarantee that
    # sorted_sequence.get_name() (used below) will exist unless we call
    # sorted_sequence.realize().
    sorted_sequence.realize()

    if sorter is not None:
        sorter.realize()

    if len(sorted_sequence.get_size()) == 1:

        def inner_fn(idx):
            val = values_loader(idx)
            return ops.bucketize(
                val,
                _boundaries_helper(sorted_sequence),
                0,
                index_dtype,
                right,
                sorter=None if sorter is None else _sorter_helper(sorter),
                sorter_indices=None if sorter is None else 0,
            )

    else:

        def inner_fn(idx):
            val = values_loader(idx)

            # Get index to the beginning of the sorted sequence within a flattened
            # version of the array.
            def get_flattened_index(tb: TensorBox):
                strides = tb.get_stride()
                return ops.index_expr(
                    functools.reduce(
                        operator.add, (s * i for s, i in zip(strides[:-1], idx[:-1]))
                    ),
                    index_dtype,
                )

            return ops.bucketize(
                val,
                _boundaries_helper(sorted_sequence),
                get_flattened_index(sorted_sequence),
                index_dtype,
                right,
                sorter=None if sorter is None else _sorter_helper(sorter),
                sorter_indices=None if sorter is None else get_flattened_index(sorter),
            )

    device = self.get_device()
    result = Pointwise.create(
        device=device,
        dtype=index_dtype,
        inner_fn=inner_fn,
        ranges=self.shape,
    )
    # see [NOTE: inductor bucketize realize]
    result.realize()

    return result
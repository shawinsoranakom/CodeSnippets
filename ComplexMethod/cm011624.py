def compare_tensor_meta(
    a: TensorLikeType,
    b: TensorLikeType,
    check_sizes=True,
    check_strides=False,
    *,
    allow_rhs_unbacked=False,
    check_conj=True,
):
    """
    Checks that two tensor likes have the same shape,
    dtype and device.

    In the future this will validate additional metadata, like
    strides.
    """
    from torch._subclasses.fake_tensor import MetadataMismatchError

    if not isinstance(a, TensorLike):
        raise AssertionError(f"a must be TensorLike, got {type(a)}")
    if not isinstance(b, TensorLike):
        raise AssertionError(f"b must be TensorLike, got {type(b)}")

    if check_sizes and not same_shape(
        a.shape, b.shape, allow_rhs_unbacked=allow_rhs_unbacked
    ):
        msg = f"Shapes {a.shape} and {b.shape} are not equal!"
        raise MetadataMismatchError(msg)

    if a.dtype != b.dtype:
        msg = f"Dtypes {a.dtype} and {b.dtype} are not equal!"
        raise MetadataMismatchError(msg)

    if a.device != b.device:
        # Handles special cuda:0 vs cuda case
        # TODO: we should review why this happens and see about fixing it
        if (str(a.device) == "cuda:0" or str(a.device) == "cuda") and (
            str(b.device) == "cuda:0" or str(b.device) == "cuda"
        ):
            pass
        else:
            msg = f"Devices {a.device} and {b.device} are not equal!"
            raise MetadataMismatchError(msg)

    # Stride checking is currently disabled, see https://github.com/pytorch/pytorch/issues/78050
    if check_strides:
        same_strides, idx = check_significant_strides(
            a, b, allow_rhs_unbacked=allow_rhs_unbacked
        )
        if not same_strides:
            msg = f"Stride mismatch! Strides are {a.stride()} and {b.stride()} (mismatched at {idx})!"
            raise MetadataMismatchError(msg)

        if a.storage_offset() != b.storage_offset():
            msg = f"Storage offset mismatch! Storage offsets are {a.storage_offset()} and {b.storage_offset()}!"
            raise MetadataMismatchError(msg)

    if check_conj:
        if a.is_conj() != b.is_conj():
            raise MetadataMismatchError(
                f"Conj mismatch! is_conj is set to {a.is_conj()} and {b.is_conj()}"
            )

    if a.is_neg() != b.is_neg():
        raise MetadataMismatchError(
            f"Neg mismatch! is_neg is set to {a.is_neg()} and {b.is_neg()}"
        )
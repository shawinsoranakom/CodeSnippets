def local_scalar_dense(
    fake_mode: FakeTensorMode, func: OpOverload, arg: FakeTensor
) -> int | float | bool | torch.SymInt | torch.SymFloat | torch.SymBool:
    if (r := arg.item_memo) is not None:
        return r
    if fake_mode.shape_env is None or (
        not fake_mode.shape_env.allow_scalar_outputs
        and not fake_mode.allow_scalar_outputs
    ):
        # Without symints/symfloats, cannot handle this
        raise DataDependentOutputException(func)
    if is_float_dtype(arg.dtype):
        r = fake_mode.shape_env.create_unbacked_symfloat()
    elif is_integer_dtype(arg.dtype):
        r = fake_mode.shape_env.create_unbacked_symint()
    elif is_boolean_dtype(arg.dtype):
        r = fake_mode.shape_env.create_unbacked_symbool()
    else:
        raise NotImplementedError(f"local_scalar_dense/item NYI for {arg.dtype}")
    arg.item_memo = r
    return r
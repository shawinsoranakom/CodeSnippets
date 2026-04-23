def _set_shape_type(
    value: ir.Value,
    meta_val: torch.Tensor
    | torch.SymBool
    | torch.SymInt
    | torch.SymFloat
    | tuple[torch.Tensor],
    complex_to_float: bool,
) -> None:
    if isinstance(meta_val, tuple):
        logger.warning("Setting shape and type of tensors is not supported yet")
    if isinstance(meta_val, torch.Tensor):
        dims = []
        shape: tuple[int, ...]
        if meta_val.dtype == torch.float4_e2m1fn_x2:
            # Change the shape to the unpacked shape
            shape = _type_casting.get_float4_shape(meta_val)
        else:
            shape = meta_val.shape
        for dim in shape:
            if isinstance(dim, int):
                dims.append(dim)
            else:
                # pyrefly: ignore [bad-argument-type]
                dims.append(str(dim.node))

        # If the dtype is set already (e.g. by the onnx_symbolic ops),
        # we don't need to set it again.
        #
        # When a user specifies complex in onnx_symbolic, we consider that to
        # be the intention even though non of the ONNX ops deals with complex values.
        # In this case, we don't change the dtype or the shape of the tensor.
        if value.dtype is None:
            value.dtype = torch_dtype_to_onnx_dtype(meta_val.dtype)
            if complex_to_float and meta_val.dtype.is_complex:
                value.dtype = torch_dtype_to_onnx_dtype(meta_val.dtype.to_real())
                # Add 2 as the last dimension if the tensor is complex to hold the real/imag parts
                dims.append(2)

        value.shape = ir.Shape(dims)
    elif isinstance(meta_val, (int, torch.SymInt)):
        # aten::sym_size output is a int, not a tensor, which stands
        # for the size of one dim. We treat it as a scalar.
        value.dtype = ir.DataType.INT64
        value.shape = ir.Shape([])
    elif isinstance(meta_val, (bool, torch.SymBool)):
        value.dtype = ir.DataType.BOOL
        value.shape = ir.Shape([])
    elif isinstance(meta_val, (float, torch.SymFloat)):
        value.dtype = ir.DataType.FLOAT
        value.shape = ir.Shape([])
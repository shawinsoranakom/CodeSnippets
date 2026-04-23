def create_rename_mapping(
    inputs, dynamic_shapes: dict[str, Any] | tuple[Any, ...] | list[Any]
) -> dict[str, str]:
    """Create a mapping from old names to new names for dynamic axes."""

    # NOTE: There's no need to handle cases where kwargs are out of order with the model signature,
    # as torch.export.export supports dynamism only when kwargs and dynamic_shapes are provided in order.
    # Reference: https://github.com/pytorch/pytorch/blob/49082f9dba3b79a344cb03652972ddbe7c3729cc/torch/export/_trace.py#L2034

    flat_dynamic_shapes, _ = _flatten_dynamic_shapes_to_axes(dynamic_shapes)
    if len(inputs) != len(flat_dynamic_shapes):
        warnings.warn(
            "# ONNX model has different number of inputs than the flatten dynamic_shapes. "
            "The dynamic axes will not be renamed.",
            UserWarning,
            stacklevel=3,
        )
        return {}
    rename_mapping: dict[str, str] = {}
    # NOTE: We assume that the flat_dynamic_shapes is in the same order as the inputs
    # When the axis is static, or it connects to _DimHint in dynamic shapes, we skip renaming
    for idx, axes in enumerate(flat_dynamic_shapes):
        input = inputs[idx]
        if isinstance(axes, dict):
            for dim, axis in axes.items():
                if not isinstance(input.shape[dim], ir.SymbolicDim):
                    continue
                old_name = input.shape[dim].value
                if old_name is None:
                    continue
                # _DimHint, int and None exists in dynamic shapes, we skip renaming
                if isinstance(axis, (_DimHint, int)) or axis is None:
                    continue
                # NOTE: ExportedProgram could give the axes the same name if they share
                # the same shape constraints.
                custom_name = _get_custom_axis_name(axis)
                if input.shape[dim].value in rename_mapping:
                    warnings.warn(
                        f"# The axis name: {custom_name} will not be used, since it shares "
                        f"the same shape constraints with another axis: {rename_mapping[input.shape[dim].value]}.",
                        stacklevel=2,
                    )
                    continue
                rename_mapping[input.shape[dim].value] = custom_name
        elif isinstance(axes, (list, tuple)):
            for dim, axis in enumerate(axes):
                if not isinstance(input.shape[dim], ir.SymbolicDim):
                    continue
                old_name = input.shape[dim].value
                if old_name is None:
                    continue
                # _DimHint, int and None exists in dynamic shapes, we skip renaming
                if isinstance(axis, (_DimHint, int)) or axis is None:
                    continue
                # NOTE: ExportedProgram could give the axes the same name if they share
                # the same shape constraints.
                custom_name = _get_custom_axis_name(axis)
                if input.shape[dim].value in rename_mapping:
                    warnings.warn(
                        f"# The axis name: {custom_name} will not be used, since it shares "
                        f"the same shape constraints with another axis: {rename_mapping[input.shape[dim].value]}.",
                        UserWarning,
                        stacklevel=3,
                    )
                    continue
                rename_mapping[input.shape[dim].value] = _get_custom_axis_name(axis)
    return rename_mapping
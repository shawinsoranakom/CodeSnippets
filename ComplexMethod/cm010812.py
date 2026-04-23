def _codegen_unwrap_subclass(
    state: _CodegenState,
    meta: SubclassCreationMeta,
    var: str,
    indent: int = 1,
    include_symints: bool = True,
) -> None:
    """Emit code to recursively unwrap a single subclass input."""
    for attr, attr_meta in meta.attrs.items():
        match attr_meta:
            case PlainTensorMeta() | OpaqueMeta():
                state.emit(
                    f"unwrapped_args.append({_safe_attr_access(var, attr)})",
                    indent=indent,
                )
            case SubclassCreationMeta():
                inner_var = state.fresh_name("_inner")
                state.emit(
                    f"{inner_var} = {_safe_attr_access(var, attr)}", indent=indent
                )
                _codegen_unwrap_subclass(
                    state,
                    attr_meta,
                    inner_var,
                    indent=indent,
                    include_symints=include_symints,
                )

    # Emit symint extraction
    if include_symints:
        size_placeholders = _compute_placeholders(meta.outer_size)
        stride_placeholders = _compute_placeholders(meta.outer_stride)
        has_size_symints = any(size_placeholders)
        has_stride_symints = any(stride_placeholders)

        if has_size_symints or has_stride_symints:
            size_var = state.fresh_name("_size")
            state.emit(f"{size_var} = {var}.size()", indent=indent)
            for i, is_sym in enumerate(size_placeholders):
                if is_sym:
                    state.emit(f"unwrapped_args.append({size_var}[{i}])", indent=indent)

            stride_var = state.fresh_name("_stride")
            state.emit(f"{stride_var} = {var}.stride()", indent=indent)
            for i, is_sym in enumerate(stride_placeholders):
                if is_sym:
                    state.emit(
                        f"unwrapped_args.append({stride_var}[{i}])", indent=indent
                    )
def dtype_match(
    torch_dtype: torch.dtype | None,
    cutlass_dtype: "cutlass_library.library.DataType",  # type: ignore[name-defined]  # noqa: F821
) -> bool:
    # Import cutlass python scripts.
    assert try_import_cutlass()
    import cutlass_library

    if torch_dtype == torch.float:
        return (
            cutlass_dtype == cutlass_library.library.DataType.f32
            or cutlass_dtype == cutlass_library.library.DataType.tf32
        )
    elif torch_dtype == torch.half:
        return cutlass_dtype == cutlass_library.library.DataType.f16
    elif torch_dtype == torch.bfloat16:
        return cutlass_dtype == cutlass_library.library.DataType.bf16
    elif torch_dtype == torch.int8:
        return cutlass_dtype == cutlass_library.library.DataType.s8
    elif torch_dtype == torch.uint8:
        return cutlass_dtype == cutlass_library.library.DataType.u8
    elif torch_dtype == torch.int32:
        return cutlass_dtype == cutlass_library.library.DataType.s32
    elif torch_dtype == torch.float8_e4m3fn:
        return cutlass_dtype == cutlass_library.library.DataType.e4m3
    elif torch_dtype == torch.float8_e5m2:
        return cutlass_dtype == cutlass_library.library.DataType.e5m2
    else:
        return False
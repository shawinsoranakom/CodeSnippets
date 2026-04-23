def to_dtype(
        x,
        dtype: torch.dtype,
        src_dtype: torch.dtype | None = None,
        use_compute_types=True,
    ):
        def _get_min_elements_per_thread(
            src_dtype: torch.dtype, dst_dtype: torch.dtype
        ) -> int:
            if src_dtype == dst_dtype:
                # No data type conversion is needed. No requirements on min_elem_per_thread.
                return 0

            # fp8 data type conversions has min_elem_per_thread requirements.
            # Refer to Triton implementations here:
            # https://github.com/triton-lang/triton/blob/10f59d8ce04052521c1bc0cb3a3f8b98918fc7e3/lib/Conversion/TritonGPUToLLVM/ElementwiseOpToLLVM.cpp#L10.
            fp8_dtypes = (
                torch.float8_e4m3fn,
                torch.float8_e5m2,
            )
            # Triton doesn't support type conversions between fp8_e4m3 and fp8_e5m2.
            assert not (
                src_dtype in fp8_dtypes
                and dst_dtype in fp8_dtypes
                and src_dtype != dst_dtype
            ), "Conversions between float8_e5m2 and float8_e4m3fn is not supported!"
            if src_dtype == torch.float8_e5m2 or dst_dtype == torch.float8_e5m2:
                return 4
            if src_dtype == torch.float8_e4m3fn or dst_dtype == torch.float8_e4m3fn:
                return 2
            # No requirements on min_elem_per_thread.
            return 0

        if src_dtype is not None:
            # Both dtype and src_dtype are set. This is used by torch to(dtype=dtype).
            # It takes the maximum min_elem_per_thread if there are multiple fp8 conversions
            # in the same kernel.
            V.kernel.min_elem_per_thread = max(
                _get_min_elements_per_thread(src_dtype, dtype),
                V.kernel.min_elem_per_thread,
            )

        if dtype == torch.bool:
            return f"({x} != 0)"
        elif dtype == torch.uint8 and (
            src_dtype is not None and src_dtype.is_floating_point or src_dtype is None
        ):
            # to work around llvm uint conversion semantics that produces 0's for negative
            # values when converting from floating types.
            # optimization - if source type is known and it's not a floating type, then
            # do not apply conversion to the intermediate type.
            return f"{x}.to(tl.int16).to(tl.uint8)"

        if use_compute_types:
            out_dtype = triton_compute_type(dtype)
        else:
            out_dtype = triton_store_type(dtype)

        return f"{x}.to({out_dtype})"
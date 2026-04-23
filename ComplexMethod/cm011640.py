def _find_highest_dtype_filtered(
        args, filter, *, float_as_complex=False
    ) -> torch.dtype | None:
        zero_dim_tensor_dtype = None
        one_plus_dim_tensor_dtype = None
        for x in args:
            if isinstance(x, TensorLike) and filter(x.dtype):
                _dtype = x.dtype
                if float_as_complex and is_float_dtype(_dtype):
                    _dtype = corresponding_complex_dtype(_dtype)
                if x.ndim == 0:
                    zero_dim_tensor_dtype = get_higher_dtype(
                        zero_dim_tensor_dtype, _dtype
                    )
                else:
                    # x.ndim > 0
                    one_plus_dim_tensor_dtype = get_higher_dtype(
                        one_plus_dim_tensor_dtype, _dtype
                    )

        # Prefers dtype of tensors with one or more dimensions
        if one_plus_dim_tensor_dtype is not None:
            return one_plus_dim_tensor_dtype

        return zero_dim_tensor_dtype
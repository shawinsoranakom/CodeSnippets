def add(
    x: torch.Tensor,
    y: torch.Tensor,
    *,
    alpha: torch.types.Number | None = None,
) -> torch.Tensor:
    # Require both x and y to be complex tensors.
    x_is_complex_tensor = torch.is_tensor(x) and x.is_complex()
    y_is_complex_tensor = torch.is_tensor(y) and y.is_complex()
    if not x_is_complex_tensor or not y_is_complex_tensor:
        return NotImplemented

    def _requires_fallback(tensor: torch.Tensor) -> bool:
        if tensor.ndim == 0:
            return False
        # Viewing complex tensors as their real dtype requires the last stride to be 1.
        return tensor.stride()[-1] != 1

    output_size_zero = False
    if x.ndim == 0 and y.ndim == 0:
        output_size_zero = True

    if x.ndim == 0:
        x = x.reshape(1)
    if y.ndim == 0:
        y = y.reshape(1)

    z = y
    if alpha is not None:
        z = alpha * y
    complex_type = torch.promote_types(x.dtype, y.dtype)

    if _requires_fallback(x) or _requires_fallback(z):
        return NotImplemented

    # For complex typed `x`, `x.view(x.real.dtype)` doubles the last dimension and can cause problem
    # when broadcasting the add.
    def reshape_tensor_complex(tensor: torch.Tensor) -> torch.Tensor:
        """Reshape tensor from [*initial_dims, last_dim] to *initial_dims, last_dim/2, 2]"""
        # Get the current shape of the tensor
        *initial_dims, last_dim = tensor.shape

        # Check if the last dimension is even. We should never reach here since `x.view(x.real.dtype)`
        # doubles the last dimension for complex numbers.
        if last_dim % 2 != 0:
            raise AssertionError(
                "The size of the last dimension must be even to reshape it to [..., last_dim/2, 2]"
            )

        # Reshape the tensor
        new_shape = (*initial_dims, last_dim // 2, 2)
        reshaped_tensor = tensor.view(new_shape)
        return reshaped_tensor

    # Manually resolve complex tensors, as .is_conj() is unreliable after cloning during compilation.
    x = x + 0
    z = z + 0

    x_reshaped = reshape_tensor_complex(x.view(x.real.dtype))
    z_reshaped = reshape_tensor_complex(z.view(y.real.dtype))
    result = torch.flatten(x_reshaped + z_reshaped, start_dim=-2).view(complex_type)

    if output_size_zero:
        return result[0]
    return result
def _validate_tensors_to_flatten(
        self, tensors: list[Tensor | nn.Parameter]
    ) -> tuple:
        """Validate the tensors to flatten and returns any necessary metadata."""
        dtype: torch.dtype | None = None
        # Return as the logical OR over each tensor's value
        flat_param_requires_grad: bool | None = None
        device: torch.device | None = None
        # For `use_orig_params=True`, permit non-uniform `requires_grad`
        for tensor in tensors:
            if isinstance(tensor, FlatParameter):
                raise ValueError("Cannot flatten a `FlatParameter`")
            if dtype is None and not tensor.is_floating_point():
                raise ValueError("Cannot flatten integer dtype tensors")
            if dtype is not None and tensor.dtype != dtype:
                raise ValueError(
                    f"Must flatten tensors with uniform dtype but got {dtype} "
                    f"and {tensor.dtype}"
                )
            if (
                not self._use_orig_params
                and flat_param_requires_grad is not None
                and tensor.requires_grad != flat_param_requires_grad
            ):
                raise ValueError(
                    "Must flatten tensors with uniform `requires_grad` when "
                    "`use_orig_params=False`"
                )
            if device is not None and tensor.device != device:
                raise ValueError(
                    "Must flatten tensors on the same device but got both "
                    f"{device} and {tensor.device}"
                )
            dtype = tensor.dtype
            flat_param_requires_grad = flat_param_requires_grad or tensor.requires_grad
            device = tensor.device
        if flat_param_requires_grad is None:
            raise AssertionError("Requires non-empty `tensors` list")
        return dtype, flat_param_requires_grad, device
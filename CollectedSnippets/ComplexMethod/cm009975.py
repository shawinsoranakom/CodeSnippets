def from_positional(
        cls, tensor: torch.Tensor, levels: list[DimEntry], has_device: bool
    ) -> _Tensor | torch.Tensor:
        """
        Create a functorch Tensor from a regular PyTorch tensor with specified dimension levels.

        This is the primary way to create Tensor objects with first-class dimensions.

        Args:
            tensor: The underlying PyTorch tensor
            levels: List of DimEntry objects specifying the dimension structure
            has_device: Whether the tensor is on a device (not CPU)

        Returns:
            A new Tensor instance with the specified dimensions, or a regular torch.Tensor
            if there are no named dimensions
        """
        seen_dims = 0
        last = 0

        for l in levels:
            if l.is_positional():
                # Validate consecutive positional dimensions
                if not (last == 0 or last + 1 == l.position()):
                    raise AssertionError(
                        f"Positional dimensions must be consecutive, got {last} then {l.position()}"
                    )
                last = l.position()
            else:
                # This is a named dimension
                seen_dims += 1

        # Validate final positional dimension
        if not (last == 0 or last == -1):
            raise AssertionError(
                f"Final positional dimension must be 0 or -1, got {last}"
            )

        if not seen_dims:
            return tensor

        # Create Tensor object with proper level management
        result = cls()
        result._tensor = tensor
        result._levels = levels
        result._has_device = has_device
        result._batchtensor = None  # Will be created lazily if needed
        result._delayed = None
        result._delayed_orig = None
        result._delayed_args = None

        # Validate tensor dimensionality matches levels
        if tensor.dim() != len(levels):
            raise AssertionError(
                f"Tensor has {tensor.dim()} dimensions but {len(levels)} levels provided"
            )

        return result
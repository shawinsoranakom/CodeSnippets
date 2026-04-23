def expand(self, *args: Dim) -> _Tensor:
        """
        Expand tensor by adding new dimensions or expanding existing dimensions.

        If all arguments are Dim objects, adds new named dimensions.
        Otherwise, falls back to regular tensor expansion behavior.

        Args:
            args: Either Dim objects for new dimensions or sizes for regular expansion

        Returns:
            New tensor with expanded dimensions

        Example:
            >>> i, j = dims()
            >>> t = torch.randn(3, 4)
            >>> expanded = t[i].expand(j, k)  # Add j, k dimensions
            >>> expanded2 = t[i].expand(2, 4)  # Regular expand with sizes
        """
        info = TensorInfo.create(self, ensure_batched=False, ensure_present=False)

        for arg in args:
            if not isinstance(arg, Dim):
                # Not all args are Dims, fallback to regular expand
                if isinstance(self, torch.Tensor) and not isinstance(self, _Tensor):
                    return torch.Tensor.expand(self, *args)
                else:
                    return self.__torch_function__(
                        torch.Tensor.expand, (type(self),), (self,) + args
                    )

        # All args are Dim objects - proceed with first-class dimension expansion
        if not info:
            # No tensor info available, fallback
            return self.__torch_function__(
                torch.Tensor.expand, (type(self),), (self,) + args
            )

        # First-class dimension expansion - all args are Dim objects
        data = info.tensor
        if data is None:
            # No tensor data available, fallback
            return self.__torch_function__(
                torch.Tensor.expand, (type(self),), (self,) + args
            )

        levels = info.levels

        new_levels: list[DimEntry] = []
        new_sizes = []
        new_strides = []

        for d in args:
            # Check if dimension already exists in current levels or new_levels
            for level in levels:
                if not level.is_positional() and level.dim() is d:
                    raise DimensionBindError(
                        f"expanding dimension {d} already exists in tensor with dims"
                    )
            for new_level in new_levels:
                if not new_level.is_positional() and new_level.dim() is d:
                    raise DimensionBindError(
                        f"expanding dimension {d} already exists in tensor with dims"
                    )

            new_levels.append(DimEntry(d))
            new_sizes.append(d.size)
            new_strides.append(0)

        # Add existing levels
        new_levels.extend(levels)

        # Add existing sizes and strides
        orig_sizes = list(data.size())
        orig_strides = list(data.stride())
        new_sizes.extend(orig_sizes)
        new_strides.extend(orig_strides)

        # Create expanded tensor using as_strided
        expanded_data = data.as_strided(new_sizes, new_strides, data.storage_offset())

        # Return new tensor with expanded dimensions
        result = Tensor.from_positional(expanded_data, new_levels, info.has_device)
        return result
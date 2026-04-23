def dim_order(self, *, ambiguity_check: bool | list[torch.memory_format] = False):
        """
        dim_order(ambiguity_check=False) -> tuple

        Returns the uniquely determined tuple of int describing the dim order or
        physical layout of :attr:`self`.

        The dim order represents how dimensions are laid out in memory of dense tensors,
        starting from the outermost to the innermost dimension.

        Note that the dim order may not always be uniquely determined.
        If `ambiguity_check` is True, this function raises a RuntimeError when the dim order cannot be uniquely determined;
        If `ambiguity_check` is a list of memory formats, this function raises a RuntimeError when tensor can not be interpreted
        into exactly one of the given memory formats, or it cannot be uniquely determined.
        If `ambiguity_check` is False, it will return one of legal dim order(s) without checking its uniqueness.
        Otherwise, it will raise TypeError.

        Args:
            ambiguity_check (bool or List[torch.memory_format]): The check method for ambiguity of dim order.

        Examples::

            >>> torch.empty((2, 3, 5, 7)).dim_order()
            (0, 1, 2, 3)
            >>> torch.empty((2, 3, 5, 7)).transpose(1, 2).dim_order()
            (0, 2, 1, 3)
            >>> torch.empty((2, 3, 5, 7), memory_format=torch.channels_last).dim_order()
            (0, 2, 3, 1)
            >>> torch.empty((1, 2, 3, 4)).dim_order()
            (0, 1, 2, 3)
            >>> try:
            ...     torch.empty((1, 2, 3, 4)).dim_order(ambiguity_check=True)
            ... except RuntimeError as e:
            ...     print(e)
            The tensor does not have unique dim order, or cannot map to exact one of the given memory formats.
            >>> torch.empty((1, 2, 3, 4)).dim_order(
            ...     ambiguity_check=[torch.contiguous_format, torch.channels_last]
            ... )  # It can be mapped to contiguous format
            (0, 1, 2, 3)
            >>> try:
            ...     torch.empty((1, 2, 3, 4)).dim_order(ambiguity_check="ILLEGAL") # type: ignore[arg-type]
            ... except TypeError as e:
            ...     print(e)
            The ambiguity_check argument must be a bool or a list of memory formats.

        .. warning::
            The dim_order tensor API is experimental and subject to change.
        """
        if has_torch_function_unary(self):
            return handle_torch_function(Tensor.dim_order, (self,), self)

        if self.is_sparse:
            raise AttributeError(
                f"Can't get dim order on sparse type: {self.type()} "
                "Use Tensor.to_dense() to convert to a dense tensor first."
            )

        # Sanity check ambiguity_check data types
        if not isinstance(ambiguity_check, bool):
            if not isinstance(ambiguity_check, list):
                raise TypeError(
                    "The ambiguity_check argument must be a bool or a list of memory formats."
                )
            for memory_format in ambiguity_check:
                if not isinstance(memory_format, torch.memory_format):
                    raise TypeError(
                        "The ambiguity_check argument must be a bool or a list of memory formats."
                    )

        def invalid_unique_memory_format(tensor, valid_memory_formats):
            """
            Returns True if the tensor cannot be uniquely mapped to any of the given memory formats, False otherwise.
            """

            n_legality = 0

            for memory_format in valid_memory_formats:
                if tensor.is_contiguous(memory_format=memory_format):
                    n_legality += 1

            return n_legality != 1

        def has_multiple_dim_order(tensor):
            """
            Returns True if there're multiple legal dim orders for given tensor, False otherwise.

            The tensor is considered to have multiple legal dim orders if either of the following conditions is met:

            * Singleton Dimensions: There's at least one singleteon dimension in the tensor.
              Since their size is 1, they don't affect the memory offset (stride * index
              is zero because index is always zero). Therefore, they can be placed anywhere
              in the dimension order without changing how data is accessed.
            * Same strides: Strides reflect how the tensor is stored in memory.
              If any two dimensions have the same stride, swapping these dimensions won't
              change how data is accessed, leading to multiple correct dimension orders.
            """
            from torch.fx.experimental.symbolic_shapes import guard_or_false

            sizes = tensor.size()
            strides = tensor.stride()

            # Check if there are any duplicate strides
            has_duplicate_strides = any(
                guard_or_false(earlier == later)
                for earlier, later in itertools.pairwise(strides)
            )

            # Check if there are any singleton dimensions
            has_singleton_dims = any(guard_or_false(size == 1) for size in sizes)

            return has_duplicate_strides or has_singleton_dims

        valid_memory_formats = (
            ambiguity_check if isinstance(ambiguity_check, list) else []
        )
        check_multiple_dim_order = (
            ambiguity_check if isinstance(ambiguity_check, bool) else True
        )

        if (
            check_multiple_dim_order and has_multiple_dim_order(self)
        ) and invalid_unique_memory_format(self, valid_memory_formats):
            raise RuntimeError(
                "The tensor does not have unique dim order, or cannot map to exact one of the given memory formats."
            )

        import torch._prims_common as utils

        out_perm, raise_ambiguity = (
            utils.compute_elementwise_output_logical_to_physical_perm(
                self, ambiguity_check=ambiguity_check
            )
        )
        if raise_ambiguity:
            raise RuntimeError("The tensor does not have unique dim order.")
        return tuple(out_perm)
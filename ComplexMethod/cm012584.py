def codegen_broadcast_and_reshape(
        self,
        value: str,
        initial_shape: Sequence[sympy.Expr],
        final_shape: Sequence[sympy.Expr],
        allow_implicit: bool,
        for_store: bool,
    ) -> str:
        """
        Generate a broadcast and a reshape for the block descriptor.
        This restores stride-0 dimensions which were removed from the block descriptor.

        Transposes are also applied to the input using self.stride_sorter:
        if for_store is True:
            - First Broadcast the value. Since self.broadcast_shape is stored in
            descending stride order, it must be reverted to the original order
            since the input value does not have dims with descending strides
            - After, transpose the broadcasted value so that dimensions are in
            descending stride order
            - Finally reshape to the block shape
        else (for load):
            - First broadcast the value to self.broadcast_shape (strides are descending)
            - Then transpose the value so that dimensions no longer have descending strides
            - Finally reshape the block to the final kernel tile shape
        """
        broadcast_shape = self.broadcast_shape
        broadcasting_dims = self.broadcasting_dims

        # If the block parameters have been sorted by descending strides,
        # permute the broadcasting parameters so that they are compatible
        # with the value being stored. This is because the dimensions
        # of the value being stored are not sorted in descending stride order,
        # but the broadcasting parameters are based on the dims in sorted order
        if for_store:
            broadcast_shape = self.stride_sorter.revert(self.broadcast_shape)
            broadcasting_dims = self.stride_sorter.revert(self.broadcasting_dims)

        # Reshape to add singletons.
        pre_broadcast_shape = [
            sympy.S.One if is_broadcasting else dim
            for dim, is_broadcasting in zip(broadcast_shape, broadcasting_dims)
        ]
        value = triton_reshape(value, initial_shape, pre_broadcast_shape)

        if (
            not self.stride_sorter.is_identity
            and not for_store
            and len(pre_broadcast_shape) == len(final_shape)
        ):
            # If all we need to do is transpose to match the final shape
            # with implicit broadcasting then we don't need an explicit broadcast
            # unless the caller requests it. So just test implicit broadcast support
            # with the transposed pre broadcast shape
            pre_broadcast_shape = self.stride_sorter.revert(pre_broadcast_shape)

        # Broadcast singletons.
        # For loads, we can often implicitly broadcast singleton dimensions.
        # We need an explicit broadcast for stores, or if the final reshape does more
        # than add singletons.
        sizevars = V.graph.sizevars
        supports_implicit_broadcast = allow_implicit and (
            len(pre_broadcast_shape) == len(final_shape)
            and all(
                sizevars.statically_known_equals(pre_dim, 1)
                or sizevars.statically_known_equals(pre_dim, post_dim)
                for pre_dim, post_dim in zip(pre_broadcast_shape, final_shape)
            )
        )

        if any(self.broadcasting_dims) and not supports_implicit_broadcast:
            value = (
                f"tl.broadcast_to({value}, {V.kernel.index_to_str(broadcast_shape)})"
            )

        old_shape = self.broadcast_shape
        if not self.stride_sorter.is_identity:
            # if for_store the transform is
            #   (non-descending strides) broadcasted kernel tile shape
            #       -> (descending strides) block descriptor shape
            # o/w if loading the transform is
            #   (descending strides) ((maybe implicitly) broadcasted block shape
            #       -> (non-descending) (maybe implicitly) broadcasted kernel tile shape
            permute_dims = (
                self.stride_sorter.sort_idx
                if for_store
                else self.stride_sorter.revert_sort_idx
            )
            value = f"tl.trans({value}, {permute_dims})"
            old_shape = (
                self.broadcast_shape
                if for_store
                else self.stride_sorter.revert(self.broadcast_shape)
            )

        # Reshape to the final shape.
        value = triton_reshape(value, old_shape, final_shape)

        return value
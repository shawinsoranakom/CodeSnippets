def _are_inputs_layout_compatible(self, layouts: list[Layout]) -> bool:
        """
        Evaluates whether input layouts are compatible for set of operations supported by this class.

        Args:
            layouts (List[Layout]): List containing Layout objects representing
                                    the input matrices.

        Returns:
            bool: True if layouts are GEMM compatible, otherwise False.
        """
        assert len(layouts) == 2 or len(layouts) == 3
        # Check if A and B are compatible
        A_layout, B_layout = layouts[:2]
        if len(A_layout.size) != 2:
            return False
        if len(B_layout.size) != 2:
            return False
        A_size = [int(i) for i in A_layout.size]
        B_size = [int(i) for i in B_layout.size]
        K = max(A_size[1], B_size[0])
        return (K == A_size[1] or K == 2 * A_size[1]) and K == B_size[0]
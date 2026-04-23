def is_stride_ordered(self, order: Sequence[int]) -> bool:
        assert len(self.stride) == len(order)

        # ignore dimensions of size 1, they dont affect layout
        non_1_indices = [
            i
            for i, dim in enumerate(self.size)
            if V.graph.sizevars.optimization_hint(dim, fallback=2) != 1
        ]

        stride = [self.stride[i] for i in non_1_indices]
        order: Sequence[int] = [order[i] for i in non_1_indices]

        def sorted_indices(arr: Sequence[int]) -> Sequence[int]:
            sorted_arr = sorted(arr)
            return [sorted_arr.index(element) for element in arr]

        # since we may have removed dimensions, need to re-sort & re-index order
        order = sorted_indices(order)

        # reorder the stride given order
        stride_ordered = [-1] * len(order)
        for i in range(len(order)):
            stride_ordered[order[i]] = stride[i]
        # check if it is in ascending order
        for i in range(len(order) - 1):
            expr = stride_ordered[i] > stride_ordered[i + 1]
            if not isinstance(expr, bool):
                expr = V.graph._shape_env.evaluate_expr(
                    stride_ordered[i] > stride_ordered[i + 1], size_oblivious=True
                )
            if expr:
                return False
        return True
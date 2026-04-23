def test_dim_order(self):
        shape = (2, 3, 5, 7)

        t = torch.empty(shape)
        self.assertSequenceEqual(t.dim_order(), (0, 1, 2, 3), seq_type=tuple)
        self.assertSequenceEqual(t.dim_order(ambiguity_check=True), (0, 1, 2, 3), seq_type=tuple)
        # transpose doesn't really change the underlying physical memory
        # so expecting dim_order change to reflect that (like strides)
        self.assertSequenceEqual(t.transpose(0, 1).dim_order(), (1, 0, 2, 3))

        t = torch.empty(shape, memory_format=torch.channels_last)
        self.assertSequenceEqual(t.dim_order(), (0, 2, 3, 1))

        t = torch.empty((2, 3, 5, 7, 8), memory_format=torch.channels_last_3d)
        self.assertSequenceEqual(t.dim_order(), (0, 2, 3, 4, 1))

        for dim_order in itertools.permutations(range(4)):
            self.assertSequenceEqual(
                dim_order, torch.empty_permuted(shape, dim_order).dim_order()
            )

        target_shapes = [[2, 2, 1, 2], [1, 2, 2, 2], [2, 2, 2, 1], [1, 2, 2, 1], [1, 2, 1, 2]]

        for shape in target_shapes:
            for memory_format in (torch.contiguous_format, torch.channels_last):
                t = torch.empty(shape).to(memory_format=memory_format)
                with self.assertRaises(RuntimeError):
                    t.dim_order(ambiguity_check=True)

                if memory_format == torch.contiguous_format:
                    dim_order_target = list(range(len(shape)))
                elif memory_format == torch.channels_last:
                    dim_order_target = [0, *list(range(2, len(shape))), 1]

                self.assertSequenceEqual(
                    dim_order_target, t.dim_order(ambiguity_check=[torch.contiguous_format, torch.channels_last])
                )


        ambiguous_shapes = [[2, 1, 2, 2], [2, 2, 1, 1], [1, 2, 1, 1], [2, 1, 1, 2], [2, 1, 2, 1],
                            [1, 1, 1, 2], [1, 1, 2, 2], [1, 1, 1, 1], [2, 1, 1, 1], [1, 1, 2, 1]]

        for shape in ambiguous_shapes:
            for memory_format in (torch.contiguous_format, torch.channels_last):
                t = torch.empty(shape).to(memory_format=memory_format)
                with self.assertRaises(RuntimeError):
                    t.dim_order(ambiguity_check=True)
                    t.dim_order(ambiguity_check=[torch.contiguous_format, torch.channels_last])

        with self.assertRaises(TypeError):
            torch.empty((1, 2, 3, 4)).dim_order(ambiguity_check="ILLEGAL_STR")

        # sparse tensor does not support dim order
        with self.assertRaises(AttributeError):
            indices = torch.tensor([[0, 1, 2], [0, 1, 2]])  # (row, column) indices
            values = torch.tensor([1.0, 2.0, 3.0])  # values at those indices
            sparse_tensor = torch.sparse_coo_tensor(indices, values, size=(3, 3))
            sparse_tensor.dim_order()
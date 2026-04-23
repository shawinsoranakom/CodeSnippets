def test_jagged_op_different_output_shape_dim(
        self, device, dtype, keepdim, requires_grad, components_require_grad, func
    ):
        """
        Operator passes when reducing on valid reduction dimensions.
        This test is for operators which return an output tensor with a shape different from the input tensor.
        """
        if get_op_name(func) == "mean" and not keepdim:
            return

        op_name = get_op_name(func)

        ts = self._get_list_for_jagged_tensor(
            ((2, 3, 4), 3, 4), device=device, requires_grad=True
        )  # (B, j0, 3, 4)

        # verify correctness of shapes (assuming that ragged_idx == 1)
        if op_name == "sum":
            reduce_dims = (
                ((0, 1), (3, 4), (1, 1, 3, 4), (0,)),  # batch, ragged
                ((2, 3), (3, None), (3, None, 1, 1), (1, 2)),  # non-batch, non-batch
                ((0, 1, 3), (3,), (1, 1, 3, 1), (0, 2)),  # batch, ragged, non-batch
                ((0, 1, 2), (4,), (1, 1, 1, 4), (0, 1)),  # batch, ragged, non-batch
                (
                    (0, 1, 2, 3),
                    (),
                    (1, 1, 1, 1),
                    (0, 1, 2),
                ),  # batch, ragged, non-batch, non-batch
                ((2,), (3, None, 4), (3, None, 1, 4), (1,)),  # non-batch
            )  # (dims, expected shape, expected keepdim shape, reduce_dim_expected), where j0 is represented as None
        elif op_name == "mean":
            reduce_dims = (
                ((2,), (3, None, 4), (3, None, 1, 4), (1,)),
                ((3,), (3, None, 3), (3, None, 3, 1), (2,)),
            )

        for rd, ref_shape_no_keepdim, ref_shape_keepdim, _ in reduce_dims:
            nt = torch.nested.as_nested_tensor(ts, layout=torch.jagged)
            out = func(nt, dim=rd, keepdim=keepdim)
            ref_shape = ref_shape_keepdim if keepdim else ref_shape_no_keepdim
            if not torch.compiler.is_compiling():  # if not using torch dynamo
                self.assertEqual(len(out.shape), len(ref_shape))
                for o, r in zip(out.shape, ref_shape):
                    if r is not None:
                        self.assertEqual(o, r)
                    else:
                        self.assertTrue(isinstance(o, torch.SymInt))

        # verify correctness of values
        tensor_lists = self._get_example_tensor_lists(
            include_list_of_lists=False,
            include_requires_grad=components_require_grad,
            include_inner_dim_size_1=True,
        )
        for tensor_list, reduce_dim_tuple in itertools.product(
            tensor_lists, reduce_dims
        ):
            nt = torch.nested.nested_tensor(
                tensor_list,
                device=device,
                dtype=dtype,
                layout=torch.jagged,
                requires_grad=requires_grad,
            )

            reduce_dim, _, _, reduce_dim_expected = reduce_dim_tuple

            if nt.dim() > reduce_dim[-1]:
                out_actual = func(nt, dim=reduce_dim, keepdim=keepdim)
                if nt._ragged_idx in reduce_dim:  # raggedness reduced away
                    out_expected = func(
                        nt.values(), dim=reduce_dim_expected, keepdim=keepdim
                    )
                    self.assertTrue(torch.allclose(out_actual, out_expected))
                else:  # raggedness preserved
                    out_expected = func(nt.values(), dim=reduce_dim_expected)
                    self.assertTrue(
                        torch.allclose(
                            out_actual.values().view(-1), out_expected.view(-1)
                        )
                    )
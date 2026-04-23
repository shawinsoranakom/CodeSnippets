def test_to_padded_tensor(self, device, dtype, nt_dim, requires_grad):
        if dtype is torch.bool and requires_grad:
            # grads not supported for bool
            return

        if nt_dim == 2:
            post_seq_len_shape = ()
        elif nt_dim == 3:
            post_seq_len_shape = (10,)
        elif nt_dim == 4:
            post_seq_len_shape = (9, 10)

        nt = torch.nested.nested_tensor(
            [
                (
                    torch.randint(
                        2, (n, *post_seq_len_shape), device=device, dtype=dtype
                    )
                    if dtype is torch.bool
                    else torch.randn(n, *post_seq_len_shape, device=device, dtype=dtype)
                )
                for n in range(2, 9)
            ],
            layout=torch.jagged,
            requires_grad=requires_grad,
        )

        PADDING_VAL = 4.2
        expected_padded = nt._values.new_full((7, 8, *post_seq_len_shape), PADDING_VAL)
        for i, component in enumerate(nt.unbind()):
            expected_padded[i, : component.shape[0]].copy_(component)

        padded = nt.to_padded_tensor(PADDING_VAL)
        self.assertEqual(expected_padded, padded)

        # convert padded dense -> NJT
        from torch.nested._internal.nested_tensor import nested_from_padded

        nt2 = nested_from_padded(padded, nt.offsets())
        self.assertEqual(nt, nt2)

        if requires_grad and dtype is not torch.bool:
            # ensure gradients flow through conversions
            nt2.backward(torch.ones_like(nt2))
            self.assertEqual(nt.grad, torch.ones_like(nt))
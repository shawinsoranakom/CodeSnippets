def test_as_nested_tensor_from_tensor(
        self, device, dtype, dim, layout, requires_grad, contiguous
    ):
        if dim == 0:
            t = torch.tensor(3.0, requires_grad=requires_grad)
        else:
            t = torch.randn(*(3 for _ in range(dim)), requires_grad=requires_grad)
        if t.dim() != dim:
            raise AssertionError(f"Expected t.dim() == {dim}, got {t.dim()}")

        if dim < 2:
            # 0-1 dim tensors can't be converted to NTs
            with self.assertRaisesRegex(
                RuntimeError, "Expected tensor argument to have dim"
            ):
                nt = torch.nested.as_nested_tensor(
                    t, device=device, dtype=dtype, layout=layout
                )
            return

        orig_t = t
        if not contiguous:
            t = t.transpose(0, 1)

        nt = torch.nested.as_nested_tensor(t, device=device, dtype=dtype, layout=layout)
        expected_dim = t.dim()
        expected_batch_size = t.size(0)
        expected_seqlen = t.size(1) if layout == torch.jagged else None
        self._validate_nt(
            nt,
            device,
            dtype,
            layout,
            requires_grad=requires_grad,
            dim=dim,
            batch_size=expected_batch_size,
            contiguous=True,
            cached_min_seqlen=expected_seqlen,
            cached_max_seqlen=expected_seqlen,
        )

        if torch.device(device) == t.device and dtype == t.dtype and contiguous:
            # should be the non-copying (view) case
            self.assertTrue(nt._is_view() and nt._base is t)

        # should have equivalent components to construction from unbound tensor list
        nt_from_unbind = torch.nested.as_nested_tensor(
            list(t.unbind(0)), device=device, dtype=dtype, layout=layout
        )
        self.assertEqualIgnoringNestedInts(nt, nt_from_unbind)

        # ensure call on a NT with the same properties returns the NT directly
        nt2 = torch.nested.as_nested_tensor(
            nt, device=device, dtype=dtype, layout=layout
        )
        self.assertTrue(nt is nt2)

        # ensure call with device=None uses input tensor device
        nt3 = torch.nested.as_nested_tensor(
            t.to(device=device, dtype=dtype),
            device=None,
            dtype=None,
            layout=layout,
        )
        self._validate_nt(
            nt3,
            device,
            dtype,
            layout,
            requires_grad=requires_grad,
            dim=dim,
            batch_size=expected_batch_size,
            contiguous=True,
            cached_min_seqlen=expected_seqlen,
            cached_max_seqlen=expected_seqlen,
        )

        # we don't support conversion between layouts this way atm
        other_layout = torch.strided if layout == torch.jagged else torch.jagged
        with self.assertRaisesRegex(
            RuntimeError, "Converting between nested tensor layouts is not supported"
        ):
            torch.nested.as_nested_tensor(
                nt, device=device, dtype=dtype, layout=other_layout
            )

        if requires_grad:
            # make sure gradients flow back into inputs
            (nt * 2).backward(torch.ones_like(nt))
            self.assertEqual(orig_t.grad, torch.ones_like(orig_t) * 2)
def test_conv_backend(
        self,
        device,
        input_shape,
        has_bias,
        strided,
        contiguous,
        transposed,
        dilated,
        groups,
        layout,
        backend_expected,
    ):
        # Build up inputs.
        dtype = torch.float32
        C_in, C_out, dim, kernel_size = input_shape[1], 12, len(input_shape) - 2, 3
        x = torch.randn(*input_shape, device=device, dtype=dtype, requires_grad=True)
        weight = torch.randn(
            C_in if transposed else C_out,
            C_out // groups if transposed else C_in // groups,
            *[kernel_size for _ in range(dim)],
            device=device,
            dtype=dtype,
            requires_grad=True,
        )
        bias = (
            torch.randn(C_out, device=device, dtype=dtype, requires_grad=True)
            if has_bias
            else None
        )

        def _make_noncontiguous(inp):
            if inp is None:
                return None
            old_requires_grad = inp.requires_grad
            inp = torch.repeat_interleave(inp, 2, dim=-1)
            inp = inp[..., ::2].detach().requires_grad_(old_requires_grad)
            return inp

        if not contiguous:
            x = _make_noncontiguous(x)
            weight = _make_noncontiguous(weight)
            bias = _make_noncontiguous(bias)

        if layout is torch._mkldnn:
            x = x.to_mkldnn()
            # Note that weight and bias are not supported as mkldnn tensors during training.

        stride = (2,) * dim if strided else (1,) * dim
        padding = (0,) * dim
        dilation = (2,) * dim if dilated else (1,) * dim
        output_padding = (0,) * dim
        inputs = [
            x,
            weight,
            bias,
            stride,
            padding,
            dilation,
            transposed,
            output_padding,
            groups,
        ]

        # Ensure correct backend is selected.
        backend_actual = torch._C._select_conv_backend(*inputs)
        self.assertEqual(backend_actual, backend_expected)

        # Ensure backward call succeeds.
        convolution = torch.ops.aten.convolution
        output = convolution(*inputs)
        grad_output = torch.randn(output.shape, device=device, dtype=dtype)
        if not contiguous:
            grad_output = _make_noncontiguous(grad_output)
        if layout is torch._mkldnn:
            grad_output = grad_output.to_mkldnn()
        output.backward(grad_output)

        # mkldnn doesn't support gradcheck :(
        if layout is torch._mkldnn:
            return

        if backend_actual != torch._C._ConvBackend.Empty:  # FIXME: forward AD fails
            # Forward AD and forward-over-reverse AD smoke test in float32
            # TODO: remove this if we introduce per-op gradient tests for float32
            with fwAD.dual_level():
                dual_inputs = [
                    (
                        fwAD.make_dual(i, torch.rand_like(i))
                        if isinstance(i, torch.Tensor)
                        else i
                    )
                    for i in inputs
                ]
                # Forward AD
                output = convolution(*dual_inputs)
                # Forward over reverse AD
                grad_output_d = fwAD.make_dual(
                    torch.rand_like(output), torch.rand_like(output)
                )
                if has_bias:
                    torch.autograd.grad(output, [x, weight, bias], grad_output_d)
                else:
                    torch.autograd.grad(output, [x, weight], grad_output_d)

        # Convert to float64 for gradcheck.
        x = x.to(torch.float64).detach().requires_grad_(True)
        weight = weight.to(torch.float64).detach().requires_grad_(True)
        if bias is not None:
            bias = bias.to(torch.float64).detach().requires_grad_(True)
        inputs = [
            x,
            weight,
            bias,
            stride,
            padding,
            dilation,
            transposed,
            output_padding,
            groups,
        ]

        # Set some backend-specific validation settings.
        gradcheck_nondet_tol = 0.0
        if torch.backends.cudnn.is_available():
            # cuDNN introduces non-determinism
            gradcheck_nondet_tol = GRADCHECK_NONDET_TOL

        self.assertTrue(gradcheck(convolution, inputs, nondet_tol=gradcheck_nondet_tol))

        # double backward doesn't support bias gradients
        if bias is not None:
            bias.requires_grad_(False)
        self.assertTrue(
            gradgradcheck(convolution, inputs, nondet_tol=gradcheck_nondet_tol)
        )
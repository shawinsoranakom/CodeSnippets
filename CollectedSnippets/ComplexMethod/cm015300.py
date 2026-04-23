def test_fused_obs_fake_quant_moving_avg(self, device, sampled_dtype, symmetric_quant, use_bool) -> None:
        """
        Tests the case where we call the fused_obs_fake_quant op multiple times
        and update the running_min and max of the activation tensors.
        """
        if device == "cpu":
            sampled_dtype = "fp32"
        dtype = {'bf16' : torch.bfloat16, 'fp16' : torch.half, 'fp32' : torch.float32}[sampled_dtype]

        in_running_min_ref = out_running_min_ref = torch.tensor(float("inf"), dtype=dtype)
        in_running_min_op = torch.tensor(float("inf"), dtype=dtype, device=device)
        in_running_max_ref = out_running_max_ref = torch.tensor(float("-inf"), dtype=dtype)
        in_running_max_op = torch.tensor(float("-inf"), dtype=dtype, device=device)
        avg_const = 0.01
        scale = torch.tensor([1.0], device=device)
        zero_point = torch.tensor([0], dtype=torch.int, device=device)
        observer_on = fake_quant_on = False if use_bool else 0

        pt_op = torch.fused_moving_avg_obs_fake_quant
        # enable observer after 2 iterations and fake_quant after 4 iterations
        for i in range(10):
            if i > 2:
                observer_on = True if use_bool else 1
            if i > 4:
                fake_quant_on = True if use_bool else 1
            x = torch.randn(5, 5, dtype=dtype, device=device)
            out = pt_op(
                x,
                torch.tensor(observer_on, device=device),
                torch.tensor(fake_quant_on, device=device),
                in_running_min_op,
                in_running_max_op,
                scale,
                zero_point,
                avg_const,
                0,
                255,
                0,
                False,
                symmetric_quant,
            )
            if observer_on:
                (
                    in_running_min_ref,
                    in_running_max_ref,
                ) = _get_tensor_min_max(
                    x,
                    running_min=in_running_min_ref,
                    running_max=in_running_max_ref,
                    averaging_const=0.01,
                    dtype=dtype,
                )

            if fake_quant_on:
                x_scale, x_zero_point = _get_scale_zp(
                    in_running_min_ref,
                    in_running_max_ref,
                    torch.quint8,
                    preserve_sparsity=symmetric_quant,
                )
                x_in = _fake_quantize_per_tensor_affine_reference(
                    x, x_scale, x_zero_point, 0, 255
                )
                self.assertEqual(scale, x_scale)
                self.assertEqual(zero_point, x_zero_point)
            else:
                x_in = x

            self.assertEqual(in_running_min_ref, in_running_min_op)
            self.assertEqual(in_running_max_ref, in_running_max_op)
            torch.testing.assert_close(out, x_in)

        # Test empty input works
        x = torch.empty(0, 5, dtype=dtype, device=device)
        out = pt_op(
            x,
            torch.tensor(1, device=device),
            torch.tensor(1, device=device),
            in_running_min_op,
            in_running_max_op,
            scale,
            zero_point,
            avg_const,
            0,
            255,
            0,
            False,
            symmetric_quant,
        )
        output_shape = (0, 5)
        self.assertEqual(out.shape, output_shape)
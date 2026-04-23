def test_fused_obs_fake_quant_moving_avg_per_channel(self, device, symmetric_quant, use_bool) -> None:
        """
        Tests the case where we call the fused_obs_fake_quant op multiple times
        and update the running_min and max of the activation tensors.
        """
        m = 5
        sizes = [[5, 5], [5, 4, 3]]
        for size in sizes:
            in_running_min_ref = torch.empty(m, device=device).fill_(float("inf"))
            in_running_min_op = torch.empty(m, device=device).fill_(float("inf"))
            in_running_max_ref = torch.empty(m, device=device).fill_(float("-inf"))
            in_running_max_op = torch.empty(m, device=device).fill_(float("-inf"))
            avg_const = 0.01

            scale = torch.empty(m, device=device).fill_(0.1)
            zero_point = torch.empty(m, dtype=torch.int, device=device).fill_(0)

            observer_on = fake_quant_on = False if use_bool else 0

            pt_op = torch.fused_moving_avg_obs_fake_quant
            # enable observer after 2 iterations and fake_quant after 4 iterations
            for i in range(10):
                if i > 2:
                    observer_on = True if use_bool else 1
                if i > 4:
                    fake_quant_on = True if use_bool else 1

                x = torch.randn(size, device=device)
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
                    True,  # per_channel_enabled
                    symmetric_quant,
                )
                if observer_on:
                    (
                        in_running_min_ref,
                        in_running_max_ref,
                    ) = _get_per_row_min_max(x, in_running_min_ref, in_running_max_ref)
                if fake_quant_on:
                    x_scale = torch.empty(m, device=device)
                    x_zero_point = torch.empty(m, dtype=torch.int, device=device)

                    for i in range(x_scale.numel()):
                        x_scale[i], x_zero_point[i] = _get_scale_zp(
                            in_running_min_ref[i].item(),
                            in_running_max_ref[i].item(),
                            torch.quint8,
                            preserve_sparsity=symmetric_quant,
                        )
                    x_in = _fake_quantize_per_channel_affine_reference(
                        x, x_scale, x_zero_point, 0, 0, 255
                    )
                    self.assertEqual(scale, x_scale)
                    self.assertEqual(zero_point, x_zero_point)
                else:
                    x_in = x
                self.assertEqual(in_running_min_ref, in_running_min_op)
                self.assertEqual(in_running_max_ref, in_running_max_op)
                torch.testing.assert_close(out, x_in)
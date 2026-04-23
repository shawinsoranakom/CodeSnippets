def test_fused_mod_per_channel(self):
        devices = ["cpu", "cuda"] if torch.cuda.is_available() else ["cpu"]
        m = 5
        n = 10
        for device in devices:
            running_min_op = torch.empty(m, device=device).fill_(float("inf"))
            running_max_op = torch.empty(m, device=device).fill_(float("-inf"))
            avg_const = 0.001
            scale = torch.empty(m, device=device).fill_(0.1)
            zero_point = torch.empty(m, dtype=torch.int, device=device).fill_(0)
            obs = FusedMovingAvgObsFakeQuantize.with_args(
                averaging_constant=avg_const,
                observer=MovingAveragePerChannelMinMaxObserver,
            )
            mod = obs()
            mod = torch.jit.script(mod)
            mod.to(device)

            for i in range(10):
                x = torch.randn(m, n, device=device)
                if i > 2:
                    mod.observer_enabled[0] = 1
                if i > 4:
                    mod.fake_quant_enabled[0] = 1
                # Run the forward on the Module
                out = mod(x)

                # Run the operator directly
                pt_op = torch.fused_moving_avg_obs_fake_quant

                out_ref = pt_op(
                    x,
                    mod.observer_enabled,
                    mod.fake_quant_enabled,
                    running_min_op,
                    running_max_op,
                    scale,
                    zero_point,
                    avg_const,
                    0,
                    255,
                    0,
                    True,
                    False,
                )
                # Compare params with reference
                torch.testing.assert_close(out, out_ref)
                if mod.observer_enabled[0]:
                    torch.testing.assert_close(
                        running_min_op, mod.activation_post_process.min_val
                    )
                    torch.testing.assert_close(
                        running_max_op, mod.activation_post_process.max_val
                    )
                if mod.fake_quant_enabled:
                    torch.testing.assert_close(scale, mod.scale)
                    torch.testing.assert_close(zero_point, mod.zero_point)

            torch.testing.assert_close(mod.state_dict()['activation_post_process.min_val'], running_min_op)
            torch.testing.assert_close(mod.state_dict()['activation_post_process.max_val'], running_max_op)
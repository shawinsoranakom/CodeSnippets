def _run_scaling_case(self, device, run, unskipped, skipped, atol=1e-7, optimizer_ctor=torch.optim.SGD, optimizer_kwargs=None):
        # Ensure scaling can be disabled without changing user control flow.
        for enabled in True, False:
            (
                mod_control, mod_scaling, opt_control, opt_scaling, data, loss_fn, skip_iter,
            ) = _create_scaling_case(device=device, optimizer_ctor=optimizer_ctor, optimizer_kwargs=optimizer_kwargs)

            # For functionality, test with a modest initial scale, and an unrealistically-large growth factor
            # so any potential errors with the growth factor handling will be magnified.
            GradScaler = partial(torch.GradScaler, device=device)
            scaler = GradScaler(init_scale=128., growth_factor=2.0, enabled=enabled, growth_interval=1)

            _ = run(device, data, mod_control, opt_control, scaler, loss_fn, skip_iter, False)
            ret = run(device, data, mod_scaling, opt_scaling, scaler, loss_fn, skip_iter, True)

            # Allows run() to optionally return a different scaler instance.
            scaler = ret if ret else scaler

            # If scaling was enabled, the scale factor should have been multiplied by the growth factor
            # len(data) - skipped times and the backoff factor "skipped" times.
            if enabled:
                net_growth = scaler.get_growth_factor()**unskipped if unskipped > 0 else 1.0
                net_backoff = scaler.get_backoff_factor()**skipped if skipped > 0 else 1.0
                self.assertTrue(scaler.get_scale() == (128. * net_growth * net_backoff))
            else:
                self.assertTrue(scaler.get_scale() == 1.0)

            for c, s in zip(mod_control.parameters(), mod_scaling.parameters()):
                self.assertEqual(c.grad, s.grad, atol=atol, rtol=1e-05)

                c_state, s_state = opt_control.state[c], opt_scaling.state[s]
                for k in c_state:
                    self.assertEqual(c_state[k], s_state[k], atol=atol, rtol=1e-05, msg=k)

                self.assertEqual(c, s, atol=atol, rtol=1e-05)
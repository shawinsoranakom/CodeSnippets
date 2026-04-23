def test_graph_scaling_fused_optimizers(self, dtype, optim_info):
        device = "xpu"
        optim_cls = optim_info.optim_cls

        steps_warmup = 3
        steps_train = 2

        optim_inputs = optim_info.optim_inputs_func(device=device)

        for optim_input in optim_inputs:
            kwargs = optim_input.kwargs
            kwargs["fused"] = True

            for actually_do_graphs in (
                (True, False) if optim_info.has_capturable_arg else (True,)
            ):
                params = [torch.randn((i + 5, i + 5), device=device) for i in range(2)]
                params_control = [p.clone().requires_grad_() for p in params]
                params_graphed = [p.clone().requires_grad_() for p in params]

                # `GradScaler` in-place updates gradients thus it's necessary to duplicate gradients.
                grads = [
                    [torch.randn_like(p) for p in params]
                    for _ in range(steps_warmup + steps_train)
                ]
                with torch.no_grad():
                    grads_control = [[g.clone() for g in gs] for gs in grads]
                    grads_graphed = [[g.clone() for g in gs] for gs in grads]

                # Gradient Scaler
                scaler_for_control = torch.amp.GradScaler("xpu", init_scale=128.0)
                with torch.no_grad():
                    scaler_for_control._lazy_init_scale_growth_tracker(device)

                scaler_for_graphed = torch.amp.GradScaler("xpu")
                scaler_for_graphed.load_state_dict(scaler_for_control.state_dict())
                with torch.no_grad():
                    scaler_for_graphed._lazy_init_scale_growth_tracker(device)

                # capturable=False
                if optim_info.has_capturable_arg:
                    kwargs["capturable"] = False
                opt = optim_cls(params_control, **kwargs)

                for i in range(steps_warmup + steps_train):
                    for j, p in enumerate(params_control):
                        p.grad = grads_control[i][j]
                    scaler_for_control.step(opt)
                    scaler_for_control.update()

                # capturable=True
                if optim_info.has_capturable_arg:
                    kwargs["capturable"] = True
                opt = optim_cls(params_graphed, **kwargs)

                for i in range(steps_warmup):
                    for j, p in enumerate(params_graphed):
                        p.grad = grads_graphed[i][j]
                    scaler_for_graphed.step(opt)
                    scaler_for_graphed.update()

                if actually_do_graphs:
                    g = torch.xpu.XPUGraph()
                    with torch.xpu.graph(g):
                        scaler_for_graphed.step(opt)
                        scaler_for_graphed.update()

                for i in range(steps_train):
                    if actually_do_graphs:
                        for j, p in enumerate(params_graphed):
                            p.grad.copy_(grads_graphed[i + steps_warmup][j])
                        g.replay()
                    else:
                        for j, p in enumerate(params_graphed):
                            p.grad = grads_graphed[i + steps_warmup][j]
                        scaler_for_graphed.step(opt)
                        scaler_for_graphed.update()

                for p_control, p_graphed in zip(params_control, params_graphed):
                    self.assertEqual(p_control, p_graphed)
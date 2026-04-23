def test_graph_optims(self, dtype, optim_info):
        device = "xpu"
        optim_cls = optim_info.optim_cls
        all_optim_inputs = _get_optim_inputs_including_global_cliquey_kwargs(
            device, dtype, optim_info, skip=("differentiable",)
        )

        steps_warmup = 3
        steps_train = 2

        for optim_input in all_optim_inputs:
            kwargs = optim_input.kwargs

            kwargs["lr"] = 0.1
            if optim_cls in (torch.optim.Adam, torch.optim.AdamW):
                kwargs["betas"] = (0.9, 0.99)

            for actually_do_graphs in (True, False):
                params = [
                    torch.randn((i + 5, i + 5), device=device) for i in range(2)
                ] + [torch.randn((), device=device)]
                params_control = [p.clone().requires_grad_() for p in params]
                params_graphed = [p.clone().requires_grad_() for p in params]

                grads = [
                    [torch.randn_like(p) for p in params]
                    for _ in range(steps_warmup + steps_train)
                ]

                # capturable=False
                kwargs["capturable"] = False

                opt = optim_cls(params_control, **kwargs)
                for i in range(steps_warmup + steps_train):
                    for j, p in enumerate(params_control):
                        p.grad = grads[i][j]
                    opt.step()

                # capturable=True
                kwargs["capturable"] = True
                opt = optim_cls(params_graphed, **kwargs)

                for i in range(steps_warmup):
                    for j, p in enumerate(params_graphed):
                        p.grad = grads[i][j]
                    opt.step()

                if actually_do_graphs:
                    g = torch.xpu.XPUGraph()
                    with torch.xpu.graph(g):
                        opt.step()

                for i in range(steps_train):
                    if actually_do_graphs:
                        for j, p in enumerate(params_graphed):
                            p.grad.copy_(grads[i + steps_warmup][j])
                        g.replay()
                    else:
                        for j, p in enumerate(params_graphed):
                            p.grad = grads[i + steps_warmup][j]
                        opt.step()

                for p_control, p_graphed in zip(params_control, params_graphed):
                    self.assertEqual(p_control, p_graphed)
def _test_graphed_optimizer(
        self, steps_warmup, steps_train, optimizer_ctor, kwargs
    ):
        for actually_do_graphs in (True, False):
            params = [torch.randn((i + 5, i + 5), device="cuda") for i in range(2)] + [
                torch.randn((), device="cuda")
            ]
            params_control = [p.clone().requires_grad_() for p in params]
            params_graphed = [p.clone().requires_grad_() for p in params]

            grads = [
                [torch.randn_like(p) for p in params]
                for _ in range(steps_warmup + steps_train)
            ]

            # Control (capturable=False)

            opt = optimizer_ctor(params_control, capturable=False, **kwargs)

            for i in range(steps_warmup + steps_train):
                for j, p in enumerate(params_control):
                    p.grad = grads[i][j]
                opt.step()

            # capturable=True

            opt = optimizer_ctor(params_graphed, capturable=True, **kwargs)

            for i in range(steps_warmup):
                for j, p in enumerate(params_graphed):
                    p.grad = grads[i][j]
                opt.step()

            if actually_do_graphs:
                g = torch.cuda.CUDAGraph()
                with torch.cuda.graph(g):
                    opt.step()

            for i in range(steps_train):
                if actually_do_graphs:
                    for j, p in enumerate(params_graphed):
                        p.grad.copy_(grads[i + steps_warmup][j])
                    g.replay()
                else:
                    # Passing capturable=True to the constructor and running without graphs should still be
                    # numerically correct, even if it's not ideal for performance.
                    for j, p in enumerate(params_graphed):
                        p.grad = grads[i + steps_warmup][j]
                    opt.step()

            for p_control, p_graphed in zip(params_control, params_graphed):
                self.assertEqual(p_control, p_graphed)
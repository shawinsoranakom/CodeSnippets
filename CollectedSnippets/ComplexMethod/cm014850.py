def test_graph_make_graphed_callables(
        self, with_amp, cache_enabled, allow_unused_input
    ):
        if self.expandable_segments:
            self.skipTest("oneDNN does not support expandable_segments memory")
        torch.manual_seed(5)
        torch.xpu.manual_seed(5)

        N, D_in, H, D_out = 640, 4096, 2048, 1024

        class MLP1(torch.nn.Module):
            def __init__(self, D_in: int, H: int, D_out: int):
                super().__init__()
                self.net_1 = torch.nn.Sequential(
                    torch.nn.Linear(D_in, H), torch.nn.Dropout(p=0.1)
                ).xpu()
                self.net_2 = torch.nn.Sequential(
                    torch.nn.Linear(H, D_out), torch.nn.Dropout(p=0.2)
                ).xpu()

            def forward(self, input_dict: dict):
                x = input_dict["x"]
                return self.net_2(self.net_1(x))

        class MLP2(torch.nn.Module):
            def __init__(self, D_in: int, H: int, D_out: int):
                super().__init__()
                self.net_1 = torch.nn.Sequential(
                    torch.nn.Linear(D_in, H), torch.nn.Dropout(p=0.1)
                ).xpu()
                self.net_2 = torch.nn.Sequential(
                    torch.nn.Linear(H, D_out), torch.nn.Dropout(p=0.2)
                ).xpu()

            def forward(self, x):
                return self.net_2(self.net_1(x))

        class ParameterlessModule(torch.nn.Module):
            def forward(self, x):
                idx = (
                    torch.arange(x.size(0), device=x.device)
                    .view(-1, 1)
                    .repeat(1, x.size(1))
                )
                return {"output": torch.gather(x, 0, idx)}

        models = []
        for _ in range(2):
            model_section1 = MLP1(D_in, H, H).xpu()
            model_section2 = MLP2(H, H, D_out).xpu()
            model_section3 = ParameterlessModule().xpu()
            models.append(
                torch.nn.Sequential(model_section1, model_section2, model_section3)
            )

        model_graphed = models[0]
        model_control = models[1]

        model_graphed.load_state_dict(model_control.state_dict())

        opt_graphed = torch.optim.SGD(model_graphed.parameters(), lr=0.1)
        opt_control = torch.optim.SGD(model_control.parameters(), lr=0.1)

        x = torch.randn(N, D_in, device="xpu")
        h = torch.randn(N, H, device="xpu", requires_grad=True)
        h2 = torch.randn(N, D_out, device="xpu", requires_grad=True)
        unused_input = torch.randn(N, H, device="xpu", requires_grad=True)
        y_pred = torch.randn(N, D_out, device="xpu", requires_grad=True)
        y = torch.randn(N, D_out, device="xpu")

        loss_fn_control = torch.nn.functional.mse_loss
        relu_control = torch.nn.functional.relu

        # This is a good stress test. It graphs four callables: two Modules and two python functions.
        with torch.amp.autocast(
            device_type="xpu", enabled=with_amp, cache_enabled=cache_enabled
        ):
            (
                model_graphed[0],
                model_graphed[1],
                model_graphed[2],
                relu_graphed,
                loss_fn_graphed,
            ) = torch.xpu.make_graphed_callables(
                (
                    model_graphed[0],
                    model_graphed[1],
                    model_graphed[2],
                    relu_control,
                    loss_fn_control,
                ),
                (
                    ({"x": x, "unused_input": unused_input},),
                    (h,),
                    (h2,),
                    (y_pred,),
                    (y_pred, y),
                ),
                allow_unused_input=allow_unused_input,
            )

        real_inputs = [torch.rand_like(x) for _ in range(10)]
        real_targets = [torch.rand_like(y) for _ in range(10)]

        for m, opt, relu, loss_fn in zip(
            (model_graphed, model_control),
            (opt_graphed, opt_control),
            (relu_graphed, relu_control),
            (loss_fn_graphed, loss_fn_control),
        ):
            # Resets RNC states before iterations for graphed and ungraphed models,
            # so dropout math should be bitwise identical for both.
            torch.manual_seed(5)
            torch.xpu.manual_seed(5)
            for data, target in zip(real_inputs, real_targets):
                opt.zero_grad(set_to_none=True)
                with torch.amp.autocast(
                    device_type="xpu", enabled=with_amp, cache_enabled=cache_enabled
                ):
                    y_pred = m({"x": data, "unused_input": unused_input})["output"]
                    y_pred = relu(y_pred)
                    loss = loss_fn(y_pred, target)
                    loss.backward()
                opt.step()

        for p, pc in zip(model_graphed.parameters(), model_control.parameters()):
            self.assertEqual(p, pc)

        # We graphed the models in training mode. Eval should still run ungraphed.
        model_graphed.eval()
        model_control.eval()
        self.assertEqual(
            model_graphed({"x": real_inputs[0]}), model_control({"x": real_inputs[0]})
        )
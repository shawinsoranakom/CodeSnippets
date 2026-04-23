def test_grad_scaling_autocast_fused_optimizers(self, device, dtype, optim_info):
        device = device.split(":")[0]
        if device not in optim_info.supports_fused_on:
            self.skipTest(
                f"{device} is not supported for fused on {optim_info.optim_cls.__name__}"
            )
        optim_inputs = optim_info.optim_inputs_func(device=device)
        optim_cls = optim_info.optim_cls
        for optim_input in optim_inputs:
            for _separate_unscale in (True, False):
                kwargs = optim_input.kwargs
                kwargs["fused"] = True
                torch.manual_seed(20)
                (
                    mod_control,
                    mod_scaling,
                    opt_control,
                    opt_scaling,
                    data,
                    loss_fn,
                    _,
                ) = _create_scaling_case(
                    optimizer_ctor=optim_cls, optimizer_kwargs=kwargs, device=device
                )
                optimizer_kwargs = deepcopy(kwargs)
                optimizer_kwargs["fused"] = False
                if "lr" not in kwargs:
                    # _create_scaling_case will set lr = 1.0 if optimizer_kwargs do not set lr
                    optimizer_kwargs["lr"] = 1.0
                opt_control = optim_cls(mod_control.parameters(), **optimizer_kwargs)
                scaler_scaling = torch.amp.GradScaler(device, init_scale=128.0)
                scaler_control = torch.amp.GradScaler(device, init_scale=128.0)

                tracker = TensorTracker()
                # Increase the tolerance for param and (max_)exp_avg_sq when betas aren't tensors
                # cuz the discrepancy between double vs float betas becomes too big. When Tensor
                # betas are used, fused and forloop both would have float betas and the default
                # tolerances are fine.
                assert_eq_kwargs = {}
                if "betas" in opt_control.param_groups[0] and not torch.is_tensor(
                    opt_control.param_groups[0]["betas"][0]
                ):
                    assert_eq_kwargs = {"atol": 2e-5, "rtol": 2e-5}
                for input, target in data:
                    opt_control.zero_grad()
                    with torch.autocast(device_type=device, dtype=torch.half):
                        output_control = mod_control(input)
                        loss_control = loss_fn(output_control, target)
                    scaler_control.scale(loss_control).backward()
                    scaler_control.step(opt_control)
                    scaler_control.update()

                    opt_scaling.zero_grad()
                    with torch.autocast(device_type=device, dtype=torch.half):
                        output_scaling = mod_scaling(input)
                        loss_scaling = loss_fn(output_scaling, target)
                    scaler_scaling.scale(loss_scaling).backward()
                    if _separate_unscale:
                        scaler_scaling.unscale_(opt_scaling)
                    scaler_scaling.step(opt_scaling)
                    scaler_scaling.update()

                    tracker.add(loss_control)
                    tracker.pop_check_set(loss_scaling, self)
                    for param_control, param_scaling in zip(
                        mod_control.parameters(), mod_scaling.parameters()
                    ):
                        tracker.add(param_control.grad)
                        tracker.pop_check_set(param_scaling.grad, self)
                        tracker.add(param_control)
                        tracker.pop_check_set(param_scaling, self, assert_eq_kwargs)

                        state_control, state_scaling = (
                            opt_control.state[param_control],
                            opt_scaling.state[param_scaling],
                        )

                        for k in state_control:
                            actual = state_scaling[k]
                            if k == "step":
                                actual = actual.squeeze()
                            tracker.add(state_control[k])
                            tracker.pop_check_set(
                                actual,
                                self,
                                assert_eq_kwargs
                                if k == "exp_avg_sq" or k == "max_exp_avg_sq"
                                else {},
                            )
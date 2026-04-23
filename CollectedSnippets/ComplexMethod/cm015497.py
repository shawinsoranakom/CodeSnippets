def _test_sharded_grad_scaler_found_inf(
        self,
        use_orig_params: bool,
        cpu_offload: CPUOffload,
    ):
        model, optim, ref_model, ref_optim = self._build_model_and_optim(
            cpu_offload=cpu_offload,
            use_orig_params=use_orig_params,
        )
        grad_scaler = ShardedGradScaler(device=device_type, init_scale=2.0)
        ref_grad_scaler = torch.amp.GradScaler(device=device_type, init_scale=2.0)
        scaled_losses: list[torch.Tensor] = []
        device = torch.device(device_type)
        torch.manual_seed(42 + self.rank + 1)

        for iter in range(10):
            for _model, _optim, _grad_scaler in (
                (ref_model, ref_optim, ref_grad_scaler),
                (model, optim, grad_scaler),
            ):
                module = _model.module
                inp = module.get_input(device)
                _optim.zero_grad()
                output = _model(*inp)
                loss = module.get_loss(inp, output)
                scaled_loss = _grad_scaler.scale(loss)
                scaled_losses.append(scaled_loss)
                scaled_loss.backward()
                orig_params = [
                    param.detach().clone()
                    for param in _model.parameters()
                    if param.grad is not None
                ]
                should_find_inf = iter % 2 == 0
                if should_find_inf and (
                    _model is ref_model or (_model is model and self.rank == 0)
                ):
                    # other ranks should find infs from rank 0
                    # after collectives
                    for param in _model.parameters():
                        if param.grad is None:
                            continue
                        param.grad.fill_(float("inf"))
                        break
                _grad_scaler.step(_optim)
                orig_scale = _grad_scaler.get_scale()
                _grad_scaler.update()
                if should_find_inf:
                    self.assertEqual(
                        _grad_scaler.get_scale(),
                        orig_scale * _grad_scaler.get_backoff_factor(),
                        (
                            f"rank: {self.rank} iter: {iter} expect origin scale {orig_scale} "
                            f"to be backed off by {_grad_scaler.get_backoff_factor()} "
                            f"but got {_grad_scaler.get_scale()}"
                        ),
                    )
                else:
                    self.assertEqual(
                        _grad_scaler.get_scale(),
                        orig_scale,
                        (
                            f"rank: {self.rank} iter: {iter} expect same scale {orig_scale} "
                            f"but got {_grad_scaler.get_scale()}"
                        ),
                    )
                for param, orig_param in zip(
                    [param for param in _model.parameters() if param.grad is not None],
                    orig_params,
                ):
                    if should_find_inf:
                        self.assertEqual(
                            param,
                            orig_param,
                            (
                                f"rank: {self.rank} iter: {iter} expect the same params before "
                                f"and after optim.step but got {param} vs {orig_param}"
                            ),
                        )
                    else:
                        self.assertNotEqual(
                            param,
                            orig_param,
                            (
                                f"rank: {self.rank} iter: {iter} expect the updated params after "
                                f"optim.step but got {param} vs {orig_param}"
                            ),
                        )
            self.assertEqual(
                scaled_losses[0],
                scaled_losses[1],
                f"iter: {iter} {scaled_losses[0]} vs {scaled_losses[1]}",
            )
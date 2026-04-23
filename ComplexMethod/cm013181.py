def _train_for_several_steps(
        self,
        model: nn.Module,
        num_steps: int,
        autocast: bool,
        lr: float = 0.01,
        fsdp_cpu_offload: CPUOffload | None = None,
        save_model: bool = False,
        mixed_precision: MixedPrecision | None = None,
        enable_sharded_grad_scaler: bool = False,
        use_pure_fp16: bool = False,
        sharded_grad_scaler_kwargs: dict[str, Any] | None = None,
    ):
        cpu_offload_params = fsdp_cpu_offload and fsdp_cpu_offload.offload_params

        model_device = next(model.parameters()).device
        if sharded_grad_scaler_kwargs is None:
            sharded_grad_scaler_kwargs = {}
        sharded_grad_scaler = ShardedGradScaler(
            enabled=enable_sharded_grad_scaler, **sharded_grad_scaler_kwargs
        )
        # use SGD with momentum instead of Adam, since Adam is scale invariant
        # and this makes it bad for tests
        optim = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9)
        for _ in range(num_steps):
            optim.zero_grad()
            with torch.amp.autocast(DEVICE_TYPE, enabled=autocast):
                # Inputs always cuda regardless of cpu offloading, or model.device
                input = model.module.get_input(torch.device(DEVICE_TYPE))  # type: ignore[operator, union-attr]
                if use_pure_fp16 or (mixed_precision and not isinstance(model, FSDP)):
                    if isinstance(input, torch.Tensor):
                        input = input.half()
                    else:
                        input = tuple(x.half() for x in input)
                output = model(*input)
                # Post-forward, if CPU offloading model param should be on CPU.
                if (
                    cpu_offload_params
                    and isinstance(model, FSDP)
                    # If not resharding after forward, the parameters are still
                    # exposed as unsharded views into the GPU flat parameter
                    and model.sharding_strategy
                    not in NO_RESHARD_AFTER_FORWARD_STRATEGIES
                ):
                    for p in model.parameters():
                        # Params should always be on CPU
                        self.assertEqual(p.device, torch.device("cpu"))

                loss = model.module.get_loss(input, output).to(model_device)  # type: ignore[operator, union-attr]
            loss = sharded_grad_scaler.scale(loss)

            if not mixed_precision and not use_pure_fp16:
                if loss.dtype != torch.float32:
                    raise AssertionError(
                        "loss data type should be float32, as the original "
                        "parameter data type is float32."
                    )
            else:
                if use_pure_fp16:
                    self.assertEqual(loss.dtype, torch.float16)
                # FSDP loss is fp16, DDP AMP loss is fp32
                elif isinstance(model, FSDP):
                    if mixed_precision is None:
                        raise AssertionError(
                            "Expected mixed_precision to not be None"
                        )  # mypy
                    self.assertEqual(loss.dtype, mixed_precision.param_dtype)
                else:
                    self.assertEqual(loss.dtype, torch.float32)
            model.module.run_backward(loss)  # type: ignore[operator, union-attr]
            # Post-backward, if CPU offloading model params should be on CPU.
            if cpu_offload_params and isinstance(model, FSDP):
                for p in model.parameters():
                    # Params should always be on CPU
                    self.assertEqual(p.device, torch.device("cpu"))
            # Unscale the gradients and step
            sharded_grad_scaler.step(optim)
            # Update the scale factor
            sharded_grad_scaler.update()
            # if save_model, simulate save + load.
            if save_model:
                state_dict = {k: v.clone() for k, v in model.state_dict().items()}
                # Zero params, if save/load state_dict did not work properly, this
                # would break the parity test with DDP.
                _zero_model(model)
                model.load_state_dict(state_dict)

        if isinstance(model, FSDP):
            model._assert_state(TrainingState.IDLE)
        return loss.detach()
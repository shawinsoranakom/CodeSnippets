def update_parameters(self, model: Module) -> None:
        """Update model parameters."""
        self_param = (
            # pyrefly: ignore [bad-argument-type]
            itertools.chain(self.module.parameters(), self.module.buffers())
            if self.use_buffers
            else self.parameters()
        )
        model_param = (
            # pyrefly: ignore [bad-argument-type]
            itertools.chain(model.parameters(), model.buffers())
            if self.use_buffers
            else model.parameters()
        )
        self_param_detached: list[Tensor | None] = []
        model_param_detached: list[Tensor | None] = []
        copy_param = bool(self.n_averaged == 0)
        for p_averaged, p_model in zip(self_param, model_param, strict=False):
            p_model_ = p_model.detach().to(p_averaged.device)
            self_param_detached.append(p_averaged.detach())
            model_param_detached.append(p_model_)
            if copy_param:
                p_averaged.detach().copy_(p_model_)

        if self.n_averaged > 0:
            if self.multi_avg_fn is not None or self.avg_fn is None:
                grouped_tensors = _group_tensors_by_device_and_dtype(
                    [self_param_detached, model_param_detached]
                )
                for (device, _), (
                    [self_params, model_params],
                    _,
                ) in grouped_tensors.items():
                    if self.multi_avg_fn:
                        self.multi_avg_fn(
                            self_params,  # type: ignore[arg-type]
                            model_params,  # type: ignore[arg-type]
                            self.n_averaged.to(device),
                        )
                    elif (
                        device is not None
                        and device.type in _get_foreach_kernels_supported_devices()
                    ):
                        multi_avg_fn = get_swa_multi_avg_fn()
                        multi_avg_fn(
                            self_params, model_params, self.n_averaged.to(device)
                        )
                    else:
                        avg_fn = get_swa_avg_fn()
                        n_averaged = self.n_averaged.to(device)
                        for p_averaged, p_model in zip(  # type: ignore[assignment]
                            self_params, model_params, strict=True
                        ):
                            # pyrefly: ignore [missing-attribute]
                            p_averaged.copy_(avg_fn(p_averaged, p_model, n_averaged))
            else:
                for p_averaged, p_model in zip(  # type: ignore[assignment]
                    self_param_detached, model_param_detached, strict=True
                ):
                    # pyrefly: ignore [missing-attribute]
                    n_averaged = self.n_averaged.to(p_averaged.device)
                    # pyrefly: ignore [missing-attribute]
                    p_averaged.detach().copy_(
                        # pyrefly: ignore [missing-attribute, bad-argument-type]
                        self.avg_fn(p_averaged.detach(), p_model, n_averaged)
                    )

        if not self.use_buffers:
            # If not apply running averages to the buffers,
            # keep the buffers in sync with the source model.
            for b_swa, b_model in zip(
                self.module.buffers(), model.buffers(), strict=True
            ):
                b_swa.detach().copy_(b_model.detach().to(b_swa.device))
        self.n_averaged += 1
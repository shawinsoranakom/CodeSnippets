def sample(
        self,
        model_wrap,
        sigmas,
        extra_args,
        callback,
        noise,
        latent_image=None,
        denoise_mask=None,
        disable_pbar=False,
    ):
        model_wrap.conds = process_cond_list(model_wrap.conds)
        cond = model_wrap.conds["positive"]
        dataset_size = sigmas.size(0)
        torch.cuda.empty_cache()
        ui_pbar = ProgressBar(self.total_steps)
        for i in (
            pbar := trange(
                self.total_steps,
                desc="Training LoRA",
                smoothing=0.01,
                disable=not comfy.utils.PROGRESS_BAR_ENABLED,
            )
        ):
            noisegen = comfy_extras.nodes_custom_sampler.Noise_RandomNoise(
                self.seed + i * 1000
            )

            if self.bucket_latents is not None:
                self._train_step_bucket_mode(model_wrap, cond, extra_args, noisegen, latent_image, pbar)
            elif self.real_dataset is None:
                self._train_step_standard_mode(model_wrap, cond, extra_args, noisegen, latent_image, dataset_size, pbar)
            else:
                self._train_step_multires_mode(model_wrap, cond, extra_args, noisegen, latent_image, dataset_size, pbar)

            if (i + 1) % self.grad_acc == 0:
                if self.grad_scaler is not None:
                    self.grad_scaler.unscale_(self.optimizer)
                for param_groups in self.optimizer.param_groups:
                    for param in param_groups["params"]:
                        if param.grad is None:
                            continue
                        param.grad.data = param.grad.data.to(param.data.dtype)
                if self.grad_scaler is not None:
                    self.grad_scaler.step(self.optimizer)
                    self.grad_scaler.update()
                else:
                    self.optimizer.step()
                self.optimizer.zero_grad()
            ui_pbar.update(1)
        torch.cuda.empty_cache()
        return torch.zeros_like(latent_image)
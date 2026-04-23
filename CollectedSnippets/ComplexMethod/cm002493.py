def _wrap_model(self, model: nn.Module, training: bool = True, dataloader: DataLoader | None = None) -> nn.Module:
        """Wrap `model` for distributed training if needed (DDP, FSDP, SageMaker, etc.)."""
        # train/eval could be run multiple-times - if already wrapped, don't re-wrap it again
        if self.accelerator.unwrap_model(model, keep_torch_compile=False) is not model:
            return model

        if is_sagemaker_mp_enabled():
            # Wrapping the base model twice in a DistributedModel will raise an error.
            if isinstance(model, smp.model.DistributedModel):
                return model
            return smp.DistributedModel(model, backward_passes_per_step=self.args.gradient_accumulation_steps)

        # Multi-gpu training, quantized models do not support DP
        if (
            self.args.n_gpu > 1
            and not getattr(model, "is_loaded_in_8bit", False)
            and not getattr(model, "is_loaded_in_4bit", False)
        ):
            model = nn.DataParallel(model)

        # Note: in torch.distributed mode, there's no point in wrapping the model
        # inside a DistributedDataParallel as we'll be under `no_grad` anyways.
        if not training:
            return model

        # Distributed training using PyTorch FSDP
        if self.is_fsdp_xla_enabled:
            model = wrap_model_xla_fsdp(model, self.args, self.is_fsdp_xla_v2_enabled)
        elif is_sagemaker_dp_enabled():
            model = nn.parallel.DistributedDataParallel(
                model, device_ids=[int(os.getenv("SMDATAPARALLEL_LOCAL_RANK"))]
            )
        return model
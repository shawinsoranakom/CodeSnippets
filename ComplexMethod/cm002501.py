def _save_optimizer_and_scheduler(self, output_dir: str) -> None:
        """Save optimizer and learning rate scheduler states to `output_dir`."""
        if is_torch_xla_available():
            xm.rendezvous("saving_optimizer_states")
            if self.is_fsdp_xla_v1_enabled:
                optm = {
                    "optimizer": self.optimizer.state_dict(),
                    "shard_metadata": self.model.get_shard_metadata(),
                }
                xm.save(
                    optm,
                    os.path.join(
                        output_dir, f"rank{self.args.process_index}-of-{self.args.world_size}-{OPTIMIZER_NAME}"
                    ),
                    master_only=False,
                )
            else:
                xm.save(self.optimizer.state_dict(), os.path.join(output_dir, OPTIMIZER_NAME))
            with warnings.catch_warnings(record=True) as caught_warnings:
                xm.save(self.lr_scheduler.state_dict(), os.path.join(output_dir, SCHEDULER_NAME))
                reissue_pt_warnings(caught_warnings)
        elif is_sagemaker_mp_enabled():
            opt_state_dict = self.optimizer.local_state_dict(gather_if_shard=False)
            smp.barrier()
            if smp.rdp_rank() == 0 or smp.state.cfg.shard_optimizer_state:
                smp.save(
                    opt_state_dict,
                    os.path.join(output_dir, OPTIMIZER_NAME),
                    partial=True,
                    v3=smp.state.cfg.shard_optimizer_state,
                )
        elif self.is_deepspeed_enabled:
            # under zero3 model file itself doesn't get saved since it's bogus! Unless deepspeed
            # config `stage3_gather_16bit_weights_on_model_save` is True
            accept_exclude_frozen_parameters = "exclude_frozen_parameters" in set(
                inspect.signature(self.model_wrapped.save_checkpoint).parameters.keys()
            )
            if accept_exclude_frozen_parameters and _is_peft_model(self.model):
                self.model_wrapped.save_checkpoint(output_dir, exclude_frozen_parameters=True)
            else:
                self.model_wrapped.save_checkpoint(output_dir)
        elif self.is_fsdp_enabled:
            # save fsdp specific ckpt for resuming from ckpt
            save_fsdp_model(
                self.accelerator.state.fsdp_plugin, self.accelerator, self.model, output_dir, **get_fsdp_ckpt_kwargs()
            )
            save_fsdp_optimizer(
                self.accelerator.state.fsdp_plugin, self.accelerator, self.optimizer, self.model, output_dir
            )
        elif self.args.should_save:
            # deepspeed.save_checkpoint above saves model/optim/sched
            torch.save(self.optimizer.state_dict(), os.path.join(output_dir, OPTIMIZER_NAME))

        # Save SCHEDULER & SCALER
        is_deepspeed_custom_scheduler = self.is_deepspeed_enabled and not isinstance(
            self.lr_scheduler, DeepSpeedSchedulerWrapper
        )
        if (
            self.args.should_save
            and (not self.is_deepspeed_enabled or is_deepspeed_custom_scheduler)
            and not is_torch_xla_available()
        ):
            with warnings.catch_warnings(record=True) as caught_warnings:
                torch.save(self.lr_scheduler.state_dict(), os.path.join(output_dir, SCHEDULER_NAME))
            reissue_pt_warnings(caught_warnings)
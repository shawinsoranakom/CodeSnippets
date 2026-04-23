def resume(self, ckpt_path: str) -> None:
        """Restore full training state from a checkpoint directory."""
        ckpt_dir = resolve_resume_checkpoint_path(ckpt_path, self._t.args.output_dir)
        if ckpt_dir is None:
            return

        if not os.path.isdir(ckpt_dir):
            raise ValueError(f"Checkpoint directory does not exist: {ckpt_dir}")

        rank = DistributedInterface().get_rank()

        metadata = load_metadata(ckpt_dir)
        self._t.global_step = metadata["global_step"]
        self._t._resume_epoch = metadata["epoch"]

        if self._dist_name in ("fsdp2", "deepspeed"):
            from ...plugins.trainer_plugins.distributed.hub import DistributedPlugin

            DistributedPlugin(self._dist_name).load_checkpoint(
                self._t.model,
                self._t.optimizer,
                ckpt_dir,
                processor=self._t.renderer.processor,
            )
        else:
            _load_standard_training_states(
                ckpt_dir,
                self._t.model,
                self._t.optimizer,
                self._t.device,
            )

        if self._dist_name != "deepspeed":
            sched_path = os.path.join(ckpt_dir, "scheduler.pt")
            if os.path.exists(sched_path):
                self._t.lr_scheduler.load_state_dict(torch.load(sched_path, map_location="cpu", weights_only=True))

        dl_path = os.path.join(ckpt_dir, "dataloader", f"rank_{rank}.pt")

        if os.path.exists(dl_path):
            self._t.train_batch_generator.load_state_dict(torch.load(dl_path, map_location="cpu", weights_only=False))
        else:
            logger.warning_rank0(
                f"Dataloader state file not found at {dl_path}. Skipping Dataloader state restoration."
            )

        if self._dist_name != "deepspeed":
            load_rng_state(ckpt_dir, rank)

        logger.info_rank0(f"Resumed from checkpoint: step={self._t.global_step}, epoch={self._t._resume_epoch}")
def save(self, epoch: int) -> None:
        """Save a full training checkpoint at the current global step."""
        ckpt_dir = os.path.join(self._t.args.output_dir, f"checkpoint-{self._t.global_step}")
        os.makedirs(ckpt_dir, exist_ok=True)

        rank = DistributedInterface().get_rank()

        if rank == 0:
            save_metadata(
                ckpt_dir,
                global_step=self._t.global_step,
                epoch=epoch,
                num_training_steps=self._t.num_training_steps,
            )

        if self._dist_name in ("fsdp2", "deepspeed"):
            from ...plugins.trainer_plugins.distributed.hub import DistributedPlugin

            DistributedPlugin(self._dist_name).save_checkpoint(
                self._t.model,
                self._t.optimizer,
                ckpt_dir,
                save_ckpt_as_hf=self._t.args.save_ckpt_as_hf,
                processor=self._t.renderer.processor,
            )
        else:
            _save_standard_training_states(
                ckpt_dir,
                self._t.model,
                self._t.optimizer,
                self._t.renderer.processor,
                self._t.args.save_ckpt_as_hf,
            )

        if self._dist_name != "deepspeed" and rank == 0:
            torch.save(self._t.lr_scheduler.state_dict(), os.path.join(ckpt_dir, "scheduler.pt"))

        dl_dir = os.path.join(ckpt_dir, "dataloader")
        os.makedirs(dl_dir, exist_ok=True)
        torch.save(
            self._t.train_batch_generator.state_dict(),
            os.path.join(dl_dir, f"rank_{rank}.pt"),
        )

        if self._dist_name != "deepspeed":
            save_rng_state(ckpt_dir, rank)

        DistributedInterface().sync()

        if rank == 0:
            mark_checkpoint_complete(ckpt_dir)
            if self._t.args.save_total_limit is not None:
                rotate_checkpoints(self._t.args.output_dir, self._t.args.save_total_limit)

        logger.info_rank0(f"Checkpoint saved to {ckpt_dir}")
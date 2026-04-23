def _finalize_training(self, trial, num_train_samples, start_time):
        """Finalize training: metrics, best-model loading, cleanup. Returns TrainOutput."""
        logger.info("\n\nTraining completed. Do not forget to share your model on huggingface.co/models =)\n\n")

        # add remaining tr_loss
        self._total_loss_scalar += self._tr_loss.item()
        effective_global_step = max(self.state.global_step, 0.001)  # Avoid ZeroDivisionError
        train_loss = self._total_loss_scalar / effective_global_step

        metrics = speed_metrics(
            "train",
            start_time,
            num_samples=num_train_samples,
            num_steps=self.state.max_steps,
        )
        self.store_flos()
        metrics["total_flos"] = self.state.total_flos
        metrics["train_loss"] = train_loss

        self._memory_tracker.stop_and_update_metrics(metrics)
        self.log(metrics)

        if self.args.load_best_model_at_end and self.state.best_model_checkpoint is not None:
            self._load_best_model()

        checkpoints_sorted = sort_checkpoints(
            output_dir=self._get_output_dir(trial), best_model_checkpoint=self.state.best_model_checkpoint
        )

        # Delete the last checkpoint when save_total_limit=1 if it's different from the best checkpoint and process allowed to save.
        if self.args.should_save and self.state.best_model_checkpoint is not None and self.args.save_total_limit == 1:
            for checkpoint in checkpoints_sorted:
                if not os.path.samefile(checkpoint, self.state.best_model_checkpoint):
                    logger.info(f"Deleting older checkpoint [{checkpoint}] due to args.save_total_limit")
                    shutil.rmtree(checkpoint, ignore_errors=True)

        self.control = self.callback_handler.on_train_end(self.args, self.state, self.control)

        # Wait for the checkpoint to be uploaded.
        self._finish_current_push()

        # After training we make sure to retrieve back the original forward pass method
        # for the embedding layer by removing the forward post hook.
        if self.neftune_noise_alpha is not None:
            deactivate_neftune(self.model, self.neftune_hook_handle, self.accelerator)
        self.is_in_train = False

        return TrainOutput(self.state.global_step, train_loss, metrics)
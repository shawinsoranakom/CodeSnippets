def on_epoch_end(self, epoch, logs=None):
        if self.monitor_op is None:
            self._set_monitor_op()  # From MonitorCallback

        # For save_freq="epoch", save at every epoch
        should_save = self.save_freq == "epoch"

        # Handle save_best_only logic
        if should_save and self.save_best_only:
            current = logs.get(self.monitor) if logs else None
            if current is None:
                warnings.warn(
                    f"Can save best model only with {self.monitor} available, "
                    f"skipping save at epoch {epoch}.",
                    stacklevel=2,
                )
                should_save = False
            elif not self._is_improvement(current, self.best):
                should_save = False
            else:
                # Update best value when there's improvement
                self.best = current

        if should_save:
            # Use epoch number as the step for Orbax save
            self._save_checkpoint(step=epoch, logs=logs)
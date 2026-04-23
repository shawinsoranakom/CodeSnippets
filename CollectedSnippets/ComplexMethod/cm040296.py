def on_epoch_end(self, epoch, logs=None):
        if self.monitor_op is None:
            # Delay setup until the model's metrics are all built
            self._set_monitor_op()
        logs = logs or {}
        logs["learning_rate"] = float(
            backend.convert_to_numpy(self.model.optimizer.learning_rate)
        )
        current = logs.get(self.monitor)

        if current is None:
            warnings.warn(
                "Learning rate reduction is conditioned on metric "
                f"`{self.monitor}` which is not available. Available metrics "
                f"are: {','.join(list(logs.keys()))}.",
                stacklevel=2,
            )
        else:
            if self.in_cooldown():
                self.cooldown_counter -= 1
                self.wait = 0

            if self._is_improvement(current, self.best):
                self.best = current
                self.wait = 0
            elif not self.in_cooldown():
                self.wait += 1
                if self.wait >= self.patience:
                    old_lr = float(
                        backend.convert_to_numpy(
                            self.model.optimizer.learning_rate
                        )
                    )
                    if old_lr > np.float32(self.min_lr):
                        new_lr = old_lr * self.factor
                        new_lr = max(new_lr, self.min_lr)
                        self.model.optimizer.learning_rate = new_lr
                        if self.verbose > 0:
                            io_utils.print_msg(
                                f"\nEpoch {epoch + 1}: "
                                "ReduceLROnPlateau reducing "
                                f"learning rate to {new_lr}."
                            )
                        self.cooldown_counter = self.cooldown
                        self.wait = 0
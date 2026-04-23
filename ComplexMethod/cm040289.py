def _should_save_model(self, epoch, batch, logs, filepath):
        """Determines whether the model should be saved.

        The model should be saved in the following cases:

        - self.save_best_only is False
        - self.save_best_only is True and `monitor` is a numpy array or
          backend tensor (falls back to `save_best_only=False`)
        - self.save_best_only is True and `self.monitor_op(current, self.best)`
          evaluates to True.

        Args:
            epoch: the epoch this iteration is in.
            batch: the batch this iteration is in. `None` if the `save_freq`
                is set to `"epoch"`.
            logs: the `logs` dict passed in to `on_batch_end` or
                `on_epoch_end`.
            filepath: the path where the model would be saved
        """
        logs = logs or {}
        if self.save_best_only:
            current = logs.get(self.monitor)
            if current is None:
                warnings.warn(
                    f"Can save best model only with {self.monitor} available.",
                    stacklevel=2,
                )
                return True
            elif (
                isinstance(current, np.ndarray) or backend.is_tensor(current)
            ) and len(current.shape) > 0:
                warnings.warn(
                    "Can save best model only when `monitor` is "
                    f"a scalar value. Received: {current}. "
                    "Falling back to `save_best_only=False`."
                )
                return True
            else:
                best_str = "None" if self.best is None else f"{self.best:.5f}"
                if self._is_improvement(current, self.best):
                    if self.verbose > 0:
                        io_utils.print_msg(
                            f"\nEpoch {epoch + 1}: {self.monitor} "
                            f"improved from {best_str} to {current:.5f}, "
                            f"saving model to {filepath}"
                        )
                    self.best = current
                    return True
                else:
                    if self.verbose > 0:
                        io_utils.print_msg(
                            f"\nEpoch {epoch + 1}: "
                            f"{self.monitor} did not improve from {best_str}"
                        )
                    return False
        else:
            if self.verbose > 0:
                io_utils.print_msg(
                    f"\nEpoch {epoch + 1}: saving model to {filepath}"
                )
            return True
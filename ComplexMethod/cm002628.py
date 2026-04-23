def step(self, metrics: float, epoch: int | None = None) -> None:
        """Perform a scheduler step based on the given metrics.

        Args:
            metrics (`float`):
                The metric value to use for LR adjustment decisions.
            epoch (`int`, *optional*):
                The current epoch number. If None, uses internal counter.
        """
        current = float(metrics)

        if self.smooth and self._streaming_avg is not None:
            current = self._streaming_avg.streamavg(current)

        if epoch is None:
            epoch = self.last_epoch + 1
        self.last_epoch = epoch

        if self.cooldown_counter > 0:
            self.cooldown_counter -= 1
            self.num_bad_epochs = 0
            self.num_good_epochs = 0
        elif self.warmup_counter > 0:
            self.warmup_counter -= 1
            self.num_bad_epochs = 0
            self.num_good_epochs = 0
        else:
            if self.is_better(current, self.best):
                self.best = current
                self.num_bad_epochs = 0
                self.num_good_epochs += 1
            else:
                self.num_bad_epochs += 1
                self.num_good_epochs = 0

            if self.num_good_epochs > self.patience:
                self._increase_lr(epoch)
                self.warmup_counter = self.warmup
                self.num_good_epochs = 0
            elif self.num_bad_epochs > self.patience:
                self._reduce_lr(epoch)
                self.cooldown_counter = self.cooldown
                self.num_bad_epochs = 0

        self._last_lr = [group["lr"] for group in self.optimizer.param_groups]
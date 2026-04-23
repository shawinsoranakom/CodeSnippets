def _test_get_last_lr(self, schedulers, targets, epochs=10):
        if isinstance(schedulers, LRScheduler):
            schedulers = [schedulers]
        optimizers = {scheduler.optimizer for scheduler in schedulers}
        for epoch in range(epochs):
            result = [scheduler.get_last_lr() for scheduler in schedulers]
            [optimizer.step() for optimizer in optimizers]
            [scheduler.step() for scheduler in schedulers]
            target = [[t[epoch] for t in targets]] * len(schedulers)
            for t, r in zip(target, result):
                self.assertEqual(
                    t,
                    r,
                    msg=f"LR is wrong in epoch {epoch}: expected {t}, got {r}",
                    atol=1e-5,
                    rtol=0,
                )
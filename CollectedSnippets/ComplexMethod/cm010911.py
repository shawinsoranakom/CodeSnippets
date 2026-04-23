def get_lr(self) -> list[float | Tensor]:
        r"""Compute the next learning rate for each of the optimizer's
        :attr:`~torch.optim.Optimizer.param_groups`.

        Finds the appropriate :attr:`_schedule_phases` entry for the current
        step and interpolates between its ``start_lr`` and ``end_lr`` using
        :meth:`_anneal_func`.

        Returns:
            list[float | Tensor]: A :class:`list` of learning rates for each of
            the optimizer's :attr:`~torch.optim.Optimizer.param_groups` with the
            same types as their current ``group["lr"]``\s.

        .. note::
            If you're trying to inspect the most recent learning rate, use
            :meth:`get_last_lr()` instead.

        .. note::
            The returned :class:`~torch.Tensor`\s are copies, and never alias
            the optimizer's ``group["lr"]``\s.

        .. note::
            When :attr:`cycle_momentum` is ``True``, this method has a side
            effect of updating the optimizer's momentum.
        """
        _warn_get_lr_called_within_step(self)

        lrs = []
        step_num = self.last_epoch

        if step_num > self.total_steps:
            raise ValueError(
                f"Tried to step {step_num} times. The specified number of total steps is {self.total_steps}"
            )

        for group in self.optimizer.param_groups:
            start_step = 0.0
            for i, phase in enumerate(self._schedule_phases):
                end_step = phase["end_step"]
                if step_num <= end_step or i == len(self._schedule_phases) - 1:
                    pct = (step_num - start_step) / (end_step - start_step)
                    computed_lr = self._anneal_func(
                        group[phase["start_lr"]], group[phase["end_lr"]], pct
                    )
                    if self.cycle_momentum:
                        computed_momentum = self._anneal_func(
                            group[phase["start_momentum"]],
                            group[phase["end_momentum"]],
                            pct,
                        )
                    break
                start_step = phase["end_step"]

            lrs.append(computed_lr)  # type: ignore[possibly-undefined]
            if self.cycle_momentum:
                if self.use_beta1:
                    group["betas"] = (computed_momentum, *group["betas"][1:])  # type: ignore[possibly-undefined]
                else:
                    group["momentum"] = computed_momentum  # type: ignore[possibly-undefined]

        return lrs
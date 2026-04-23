def get_lr(self) -> list[float | Tensor]:
        r"""Compute the next learning rate for each of the optimizer's
        :attr:`~torch.optim.Optimizer.param_groups`.

        Advances each ``group["lr"]`` in the optimizer's
        :attr:`~torch.optim.Optimizer.param_groups` along a cycle between the
        group's ``base_lr`` and ``max_lr`` using :meth:`scale_fn`.

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
            This method treats :attr:`last_epoch` as the index of the previous
            batch.

        .. note::
            When :attr:`cycle_momentum` is ``True``, this method has a side
            effect of updating the optimizer's momentum.
        """
        _warn_get_lr_called_within_step(self)

        cycle = math.floor(1 + self.last_epoch / self.total_size)
        x = 1.0 + self.last_epoch / self.total_size - cycle
        if x <= self.step_ratio:
            scale_factor = x / self.step_ratio
        else:
            scale_factor = (x - 1) / (self.step_ratio - 1)

        lrs = []
        for base_lr, max_lr in zip(self.base_lrs, self.max_lrs, strict=True):
            base_height = (max_lr - base_lr) * scale_factor
            if self.scale_mode == "cycle":
                lr = base_lr + base_height * self.scale_fn(cycle)
            else:
                lr = base_lr + base_height * self.scale_fn(self.last_epoch)
            lrs.append(lr)

        if self.cycle_momentum:
            momentums = []
            for base_momentum, max_momentum in zip(
                self.base_momentums, self.max_momentums, strict=True
            ):
                base_height = (max_momentum - base_momentum) * scale_factor
                if self.scale_mode == "cycle":
                    momentum = max_momentum - base_height * self.scale_fn(cycle)
                else:
                    momentum = max_momentum - base_height * self.scale_fn(
                        self.last_epoch
                    )
                momentums.append(momentum)
            for param_group, momentum in zip(
                self.optimizer.param_groups, momentums, strict=True
            ):
                if self.use_beta1:
                    param_group["betas"] = (momentum, *param_group["betas"][1:])
                else:
                    param_group["momentum"] = momentum

        return lrs
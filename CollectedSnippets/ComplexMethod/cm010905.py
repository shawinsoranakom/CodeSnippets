def __init__(
        self,
        optimizer: Optimizer,
        schedulers: list[LRScheduler],
        milestones: list[int],
        last_epoch: int = -1,
    ) -> None:
        if len(schedulers) < 1:
            raise ValueError(
                f"{self.__class__.__name__} expects at least one scheduler, but got no scheduler."
            )

        for scheduler_idx, scheduler in enumerate(schedulers):
            if not hasattr(scheduler, "optimizer"):
                raise TypeError(
                    f"{self.__class__.__name__} at index {scheduler_idx} should have `optimizer` as its attribute."
                )
            if isinstance(scheduler, ReduceLROnPlateau):
                raise ValueError(
                    f"{self.__class__.__name__} does not support `ReduceLROnPlateau` scheduler as it "
                    "requires additional kwargs to be specified when calling `step`, "
                    f"but got one at index {scheduler_idx} in the given schedulers sequence."
                )
            if optimizer != scheduler.optimizer:
                raise ValueError(
                    f"{self.__class__.__name__} expects all schedulers to belong to the same optimizer, but "
                    f"got scheduler {scheduler.__class__.__name__} at index {scheduler_idx} has {scheduler.optimizer}, "
                    f"which is different from {optimizer.__class__.__name__}."
                )

        if len(milestones) != len(schedulers) - 1:
            raise ValueError(
                "Sequential Schedulers expects number of schedulers provided to be one more "
                f"than the number of milestone points, but got number of schedulers {len(schedulers)} and the "
                f"number of milestones to be equal to {len(milestones)}"
            )
        self._schedulers = schedulers
        self._milestones = milestones
        self.last_epoch = last_epoch + 1
        self.optimizer = optimizer

        # Reset learning rates back to initial values
        for group in self.optimizer.param_groups:
            _update_param_group_val(group, "lr", group["initial_lr"])

        # "Undo" the step performed by other schedulers
        self.recursive_undo()

        # Perform the initial step for only the first scheduler
        self._schedulers[0]._initial_step()

        self._last_lr = schedulers[0].get_last_lr()
def __init__(self, period_group_size_dict=None, warmup_steps=0, process_group=None):
        super().__init__(process_group)
        if not period_group_size_dict:
            raise ValueError("Arg ``period_group_size_dict`` must not be empty.")
        self._periods = list(period_group_size_dict.keys())
        if self._periods[0] <= 0:
            raise ValueError(
                "The minimum period in arg ``period_group_size_dict`` must be a positive value."
            )
        elif self._periods[-1] == 1:
            warnings.warn(
                "When the maximum period in arg ``period_group_size_dict`` is 1, "
                "no need to use model averaging because the communication cost "
                "of all-reducing parameters will be no less than the cost of all-reducing gradients "
                "by DistributedDataParallel in the backward pass. Therefore, only "
                "DistributedDataParallel should be used for this case.",
                stacklevel=2,
            )
        overall_group_size = dist.get_world_size(group=self.process_group)
        if list(period_group_size_dict.values())[-1] != overall_group_size:
            raise ValueError(
                f"The last value in arg ``period_process_group_dict`` {list(period_group_size_dict.values())[-1]} "
                f"must be equal to the size of arg ``process_group`` {overall_group_size}."
            )

        self.period_process_group_dict = OrderedDict()
        logger.info("Model averaging hierarchy:")
        for period, group_size in period_group_size_dict.items():
            logger.info(
                "\tEach group that has %s processes average parameters every %s iterations, "
                "if no higher-level averaging.",
                group_size,
                period,
            )
            if group_size != overall_group_size:
                self.period_process_group_dict[period], _ = dist.new_subgroups(
                    group_size=group_size, group=self.process_group
                )
            else:
                self.period_process_group_dict[period] = self.process_group

        if warmup_steps < 0:
            raise ValueError("Arg ``warmup_steps`` must be a non-negative number.")
        self.warmup_steps = warmup_steps
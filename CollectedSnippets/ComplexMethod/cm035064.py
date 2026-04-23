def __init__(
        self,
        max_lr,
        epochs=None,
        steps_per_epoch=None,
        pct_start=0.3,
        anneal_strategy="cos",
        div_factor=25.0,
        final_div_factor=1e4,
        three_phase=False,
        last_epoch=-1,
        verbose=False,
    ):
        # Validate total_steps
        if epochs <= 0 or not isinstance(epochs, int):
            raise ValueError(
                "Expected positive integer epochs, but got {}".format(epochs)
            )
        if steps_per_epoch <= 0 or not isinstance(steps_per_epoch, int):
            raise ValueError(
                "Expected positive integer steps_per_epoch, but got {}".format(
                    steps_per_epoch
                )
            )
        self.total_steps = epochs * steps_per_epoch

        self.max_lr = max_lr
        self.initial_lr = self.max_lr / div_factor
        self.min_lr = self.initial_lr / final_div_factor

        if three_phase:
            self._schedule_phases = [
                {
                    "end_step": float(pct_start * self.total_steps) - 1,
                    "start_lr": self.initial_lr,
                    "end_lr": self.max_lr,
                },
                {
                    "end_step": float(2 * pct_start * self.total_steps) - 2,
                    "start_lr": self.max_lr,
                    "end_lr": self.initial_lr,
                },
                {
                    "end_step": self.total_steps - 1,
                    "start_lr": self.initial_lr,
                    "end_lr": self.min_lr,
                },
            ]
        else:
            self._schedule_phases = [
                {
                    "end_step": float(pct_start * self.total_steps) - 1,
                    "start_lr": self.initial_lr,
                    "end_lr": self.max_lr,
                },
                {
                    "end_step": self.total_steps - 1,
                    "start_lr": self.max_lr,
                    "end_lr": self.min_lr,
                },
            ]

        # Validate pct_start
        if pct_start < 0 or pct_start > 1 or not isinstance(pct_start, float):
            raise ValueError(
                "Expected float between 0 and 1 pct_start, but got {}".format(pct_start)
            )

        # Validate anneal_strategy
        if anneal_strategy not in ["cos", "linear"]:
            raise ValueError(
                "anneal_strategy must by one of 'cos' or 'linear', instead got {}".format(
                    anneal_strategy
                )
            )
        elif anneal_strategy == "cos":
            self.anneal_func = self._annealing_cos
        elif anneal_strategy == "linear":
            self.anneal_func = self._annealing_linear

        super(OneCycleDecay, self).__init__(max_lr, last_epoch, verbose)
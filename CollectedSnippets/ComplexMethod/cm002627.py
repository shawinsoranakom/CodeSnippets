def __init__(
        self,
        optimizer: Optimizer,
        mode: str = "min",
        factor: float = 0.95,
        patience: int = 10,
        threshold: float = 1e-6,
        threshold_mode: str = "abs",
        cooldown: int = 0,
        warmup: int = 0,
        min_lr: float | list[float] = 1e-3,
        max_lr: float | list[float] = 1.0,
        eps: float = 1e-8,
        verbose: bool = False,
        smooth: bool = False,
        window_size: int = 50,
        reset_start: int = 500,
    ) -> None:
        if factor >= 1.0:
            raise ValueError("Factor should be < 1.0.")
        if not isinstance(optimizer, Optimizer):
            raise TypeError(f"{type(optimizer).__name__} is not an Optimizer")

        self.optimizer = optimizer
        self.factor = factor
        self.patience = patience
        self.verbose = verbose
        self.cooldown = cooldown
        self.warmup = warmup
        self.cooldown_counter = 0
        self.warmup_counter = 0
        self.mode = mode
        self.threshold = threshold
        self.threshold_mode = threshold_mode
        self.eps = eps
        self.smooth = smooth
        self.window_size = window_size
        self.reset_start = reset_start
        self.reset_start_original = reset_start
        self.last_epoch = 0

        if isinstance(min_lr, (list, tuple)):
            if len(min_lr) != len(optimizer.param_groups):
                raise ValueError(f"expected {len(optimizer.param_groups)} min_lrs, got {len(min_lr)}")
            self.min_lrs = list(min_lr)
        else:
            self.min_lrs = [min_lr] * len(optimizer.param_groups)

        if isinstance(max_lr, (list, tuple)):
            if len(max_lr) != len(optimizer.param_groups):
                raise ValueError(f"expected {len(optimizer.param_groups)} max_lrs, got {len(max_lr)}")
            self.max_lrs = list(max_lr)
        else:
            self.max_lrs = [max_lr] * len(optimizer.param_groups)

        self._init_lrs = [group["lr"] for group in optimizer.param_groups]
        self._last_lr = self._init_lrs.copy()

        self.best: float = float("inf") if mode == "min" else float("-inf")
        self.num_bad_epochs = 0
        self.num_good_epochs = 0

        if mode not in ("min", "max"):
            raise ValueError(f"mode {mode} is unknown!")
        if threshold_mode not in ("rel", "abs"):
            raise ValueError(f"threshold mode {threshold_mode} is unknown!")

        self._streaming_avg: StreamingAverage | None = None
        if smooth:
            self._streaming_avg = StreamingAverage(window_size)
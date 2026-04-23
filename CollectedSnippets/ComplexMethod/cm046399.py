def __init__(
        self,
        iterable: Any = None,
        desc: str | None = None,
        total: int | None = None,
        leave: bool = True,
        file: IO[str] | None = None,
        mininterval: float = 0.1,
        disable: bool | None = None,
        unit: str = "it",
        unit_scale: bool = True,
        unit_divisor: int = 1000,
        bar_format: str | None = None,  # kept for API compatibility; not used for formatting
        initial: int = 0,
        **kwargs,
    ) -> None:
        """Initialize the TQDM progress bar with specified configuration options.

        Args:
            iterable (Any, optional): Iterable to wrap with progress bar.
            desc (str, optional): Prefix description for the progress bar.
            total (int, optional): Expected number of iterations.
            leave (bool, optional): Whether to leave the progress bar after completion.
            file (IO[str], optional): Output file stream for progress display.
            mininterval (float, optional): Minimum time interval between updates (default 0.1s, 60s in GitHub Actions).
            disable (bool, optional): Whether to disable the progress bar. Auto-detected if None.
            unit (str, optional): String for units of iteration (default "it" for items).
            unit_scale (bool, optional): Auto-scale units for bytes/data units.
            unit_divisor (int, optional): Divisor for unit scaling (default 1000).
            bar_format (str, optional): Custom bar format string.
            initial (int, optional): Initial counter value.
            **kwargs (Any): Additional keyword arguments for compatibility (ignored).
        """
        # Disable if not verbose
        if disable is None:
            try:
                from ultralytics.utils import LOGGER, VERBOSE

                disable = not VERBOSE or LOGGER.getEffectiveLevel() > 20
            except ImportError:
                disable = False

        self.iterable = iterable
        self.desc = desc or ""
        self.total = total or (len(iterable) if hasattr(iterable, "__len__") else None) or None  # prevent total=0
        self.disable = disable
        self.unit = unit
        self.unit_scale = unit_scale
        self.unit_divisor = unit_divisor
        self.leave = leave
        self.noninteractive = is_noninteractive_console()
        self.mininterval = max(mininterval, self.NONINTERACTIVE_MIN_INTERVAL) if self.noninteractive else mininterval
        self.initial = initial

        # Kept for API compatibility (unused for f-string formatting)
        self.bar_format = bar_format

        self.file = file or sys.stdout

        # Internal state
        self.n = self.initial
        self.last_print_n = self.initial
        self.last_print_t = time.time()
        self.start_t = time.time()
        self.last_rate = 0.0
        self.closed = False
        self.is_bytes = unit_scale and unit in {"B", "bytes"}
        self.scales = (
            [(1073741824, "GB/s"), (1048576, "MB/s"), (1024, "KB/s")]
            if self.is_bytes
            else [(1e9, f"G{self.unit}/s"), (1e6, f"M{self.unit}/s"), (1e3, f"K{self.unit}/s")]
        )

        if not self.disable and self.total and not self.noninteractive:
            self._display()
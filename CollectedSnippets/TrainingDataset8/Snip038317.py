def __init__(
        self,
        md5: str,
        modification_time: float,
        *,  # keyword-only arguments:
        glob_pattern: Optional[str] = None,
        allow_nonexistent: bool = False,
    ):
        self.md5 = md5
        self.modification_time = modification_time

        self.glob_pattern = glob_pattern
        self.allow_nonexistent = allow_nonexistent

        self.on_changed = Signal()
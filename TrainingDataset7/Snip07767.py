def __init__(
        self, *expressions, autosummarize=None, pages_per_range=None, **kwargs
    ):
        if pages_per_range is not None and pages_per_range <= 0:
            raise ValueError("pages_per_range must be None or a positive integer")
        self.autosummarize = autosummarize
        self.pages_per_range = pages_per_range
        super().__init__(*expressions, **kwargs)
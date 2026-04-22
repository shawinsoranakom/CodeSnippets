def __init__(
        self,
        func: types.FunctionType,
        show_spinner: Union[bool, str],
        suppress_st_warning: bool,
        persist: Optional[str],
        max_entries: Optional[int],
        ttl: Optional[float],
        allow_widgets: bool,
    ):
        super().__init__(func, show_spinner, suppress_st_warning, allow_widgets)
        self.persist = persist
        self.max_entries = max_entries
        self.ttl = ttl
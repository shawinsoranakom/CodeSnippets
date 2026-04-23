def __call__(
        self,
        *,
        persist: Optional[str] = None,
        show_spinner: Union[bool, str] = True,
        suppress_st_warning: bool = False,
        max_entries: Optional[int] = None,
        ttl: Optional[Union[float, timedelta]] = None,
        experimental_allow_widgets: bool = False,
    ) -> Callable[[F], F]:
        ...
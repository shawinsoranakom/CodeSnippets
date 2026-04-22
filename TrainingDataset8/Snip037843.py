def __call__(
        self,
        *,
        show_spinner: Union[bool, str] = True,
        suppress_st_warning=False,
        experimental_allow_widgets: bool = False,
    ) -> Callable[[F], F]:
        ...
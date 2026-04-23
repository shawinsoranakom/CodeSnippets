def __init__(
        self,
        func: types.FunctionType,
        show_spinner: Union[bool, str],
        suppress_st_warning: bool,
        allow_widgets: bool,
    ):
        self.func = func
        self.show_spinner = show_spinner
        self.suppress_st_warning = suppress_st_warning
        self.allow_widgets = allow_widgets
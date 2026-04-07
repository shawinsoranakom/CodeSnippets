def __init__(
        self, *, missing_args_message=None, called_from_command_line=None, **kwargs
    ):
        self.missing_args_message = missing_args_message
        self.called_from_command_line = called_from_command_line
        if PY314:
            if not PY315:
                kwargs.setdefault("suggest_on_error", True)
            if os.environ.get("DJANGO_COLORS") == "nocolor" or "--no-color" in sys.argv:
                kwargs.setdefault("color", False)
        super().__init__(**kwargs)
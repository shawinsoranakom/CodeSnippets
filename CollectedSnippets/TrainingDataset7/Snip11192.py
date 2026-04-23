def __init__(
        self, verbose_name=None, name=None, auto_now=False, auto_now_add=False, **kwargs
    ):
        self.auto_now, self.auto_now_add = auto_now, auto_now_add
        if auto_now or auto_now_add:
            kwargs["editable"] = False
            kwargs["blank"] = True
        super().__init__(verbose_name, name, **kwargs)
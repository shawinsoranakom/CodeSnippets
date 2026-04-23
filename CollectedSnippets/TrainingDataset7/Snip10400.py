def __init__(
        self, code, reverse_code=None, atomic=None, hints=None, elidable=False
    ):
        self.atomic = atomic
        # Forwards code
        if not callable(code):
            raise ValueError("RunPython must be supplied with a callable")
        self.code = code
        # Reverse code
        if reverse_code is None:
            self.reverse_code = None
        else:
            if not callable(reverse_code):
                raise ValueError("RunPython must be supplied with callable arguments")
            self.reverse_code = reverse_code
        self.hints = hints or {}
        self.elidable = elidable
def __init__(self, level, msg, hint=None, obj=None, id=None):
        if not isinstance(level, int):
            raise TypeError("The first argument should be level.")
        self.level = level
        self.msg = msg
        self.hint = hint
        self.obj = obj
        self.id = id
def __new__(cls, value, setting):
        self = tuple.__new__(cls, value)
        self.setting = setting
        return self
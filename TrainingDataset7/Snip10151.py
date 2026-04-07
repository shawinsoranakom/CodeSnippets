def __init__(self, key, origin, error_message):
        super().__init__(key)
        self.origin = origin
        self.error_message = error_message
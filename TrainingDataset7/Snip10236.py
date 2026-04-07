def __init__(self, model_name, name, field, preserve_default=True):
        self.preserve_default = preserve_default
        super().__init__(model_name, name, field)
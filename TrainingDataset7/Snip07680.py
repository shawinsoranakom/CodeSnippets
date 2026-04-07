def __init__(self, index, base_field, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = index
        self.base_field = base_field
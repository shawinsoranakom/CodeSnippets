def __call__(self, *args, **kwargs):
        return IndexTransform(self.index, self.base_field, *args, **kwargs)
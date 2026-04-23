def __call__(self, *args, **kwargs):
        return SliceTransform(self.start, self.end, *args, **kwargs)
def encode(self, *args, **kwargs):
        type(self).calls += 1
        return super().encode(*args, **kwargs)
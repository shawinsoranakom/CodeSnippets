def __init__(self, wkt, **kwargs):
        self.wkt = wkt
        for key, value in kwargs.items():
            setattr(self, key, value)
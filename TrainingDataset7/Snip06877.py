def __init__(self, attrs=None):
        if attrs is None:
            attrs = {}
        attrs.setdefault("default_lon", self.default_lon)
        attrs.setdefault("default_lat", self.default_lat)
        attrs.setdefault("default_zoom", self.default_zoom)
        super().__init__(attrs=attrs)
def __init__(self, attrs=None):
        self.attrs = {
            key: getattr(self, key)
            for key in ("base_layer", "geom_type", "map_srid", "display_raw")
        }
        if attrs:
            self.attrs.update(attrs)
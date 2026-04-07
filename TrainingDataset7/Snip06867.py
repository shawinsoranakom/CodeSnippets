def __init__(self, *, srid=None, geom_type=None, **kwargs):
        self.srid = srid
        if geom_type is not None:
            self.geom_type = geom_type
        super().__init__(**kwargs)
        self.widget.attrs["geom_type"] = self.geom_type
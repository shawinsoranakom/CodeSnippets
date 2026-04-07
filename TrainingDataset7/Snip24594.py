def __init__(self, name, *, ext="shp", **kwargs):
        # Shapefile is default extension, unless specified otherwise.
        self.name = name
        self.ds = get_ds_file(name, ext)
        super().__init__(**kwargs)
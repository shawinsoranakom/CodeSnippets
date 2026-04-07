def __init__(self, source, index):
        self.source = source
        self._ptr = capi.get_ds_raster_band(source._ptr, index)
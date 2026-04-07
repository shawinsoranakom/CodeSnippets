def __len__(self):
        return capi.get_ds_raster_count(self.source._ptr)
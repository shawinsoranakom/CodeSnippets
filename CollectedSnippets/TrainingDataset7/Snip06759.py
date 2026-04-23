def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Always include SRID for less fragility; include spatial index if it's
        # not the default value.
        kwargs["srid"] = self.srid
        if self.spatial_index is not True:
            kwargs["spatial_index"] = self.spatial_index
        return name, path, args, kwargs
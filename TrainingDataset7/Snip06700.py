def _create_index_sql(self, model, *, fields=None, **kwargs):
        if fields is None or len(fields) != 1 or not hasattr(fields[0], "geodetic"):
            return super()._create_index_sql(model, fields=fields, **kwargs)

        return self._create_spatial_index_sql(model, fields[0], **kwargs)
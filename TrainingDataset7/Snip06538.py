def supports_extent_aggr(self):
        return models.Extent not in self.connection.ops.disallowed_aggregates
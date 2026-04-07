def spatial_aggregate_name(self, agg_name):
        return getattr(self, agg_name.lower())
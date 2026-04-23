def spatial_aggregate_name(self, agg_name):
        """
        Return the spatial aggregate SQL name.
        """
        agg_name = "unionagg" if agg_name.lower() == "union" else agg_name.lower()
        return getattr(self, agg_name)
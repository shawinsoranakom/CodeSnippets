def spatial_aggregate_name(self, agg_name):
        """
        Return the spatial aggregate SQL template and function for the
        given Aggregate instance.
        """
        agg_name = "unionagg" if agg_name.lower() == "union" else agg_name.lower()
        return getattr(self, agg_name)
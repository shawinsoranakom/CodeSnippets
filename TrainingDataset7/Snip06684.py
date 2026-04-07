def spatial_aggregate_name(self, agg_name):
        if agg_name == "Extent3D":
            return self.extent3d
        else:
            return self.geom_func_prefix + agg_name
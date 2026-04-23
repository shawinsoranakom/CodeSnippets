def collect(self):
        if self.connection.features.supports_collect_aggr:
            return self.geom_func_prefix + "Collect"
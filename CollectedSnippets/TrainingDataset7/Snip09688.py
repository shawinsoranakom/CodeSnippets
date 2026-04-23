def supports_aggregation_over_interval_types(self):
        return self.connection.oracle_version >= (23,)
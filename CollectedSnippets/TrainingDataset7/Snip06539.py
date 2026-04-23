def supports_make_line_aggr(self):
        return models.MakeLine not in self.connection.ops.disallowed_aggregates
def as_sql(self, *args, **kwargs):
        if not self.source_expressions:
            return "", ()
        return super().as_sql(*args, **kwargs)
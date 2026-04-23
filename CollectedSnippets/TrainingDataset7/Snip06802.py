def as_sqlite(self, compiler, connection, **extra_context):
        clone = self.copy()
        clone.set_source_expressions([self.get_source_expressions()[0]])
        return super(BoundingCircle, clone).as_sqlite(
            compiler, connection, **extra_context
        )
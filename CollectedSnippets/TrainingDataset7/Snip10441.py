def record_applied(self, app, name):
        """Record that a migration was applied."""
        self.ensure_schema()
        self.migration_qs.create(app=app, name=name)
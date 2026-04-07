def record_unapplied(self, app, name):
        """Record that a migration was unapplied."""
        self.ensure_schema()
        self.migration_qs.filter(app=app, name=name).delete()
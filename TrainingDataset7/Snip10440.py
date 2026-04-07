def applied_migrations(self):
        """
        Return a dict mapping (app_name, migration_name) to Migration instances
        for all applied migrations.
        """
        if self.has_table():
            return {
                (migration.app, migration.name): migration
                for migration in self.migration_qs
            }
        else:
            # If the django_migrations table doesn't exist, then no migrations
            # are applied.
            return {}
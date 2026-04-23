def record_migration(self, app_label, name, forward=True):
        migration = self.loader.disk_migrations.get((app_label, name))
        # For replacement migrations, record individual statuses
        if migration and migration.replaces:
            for replaced_app_label, replaced_name in migration.replaces:
                self.record_migration(replaced_app_label, replaced_name, forward)
        if forward:
            self.recorder.record_applied(app_label, name)
        else:
            self.recorder.record_unapplied(app_label, name)
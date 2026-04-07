def _resolve_replaced_migration_keys(self, migration):
        resolved_keys = set()
        for migration_key in set(migration.replaces):
            migration_entry = self.disk_migrations.get(migration_key)
            if migration_entry and migration_entry.replaces:
                replace_keys = self._resolve_replaced_migration_keys(migration_entry)
                resolved_keys.update(replace_keys)
            else:
                resolved_keys.add(migration_key)
        return resolved_keys
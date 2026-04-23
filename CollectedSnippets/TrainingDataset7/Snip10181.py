def replace_migration(self, migration_key):
        if completed_replacement := self.replacements_progress.get(migration_key, None):
            return
        elif completed_replacement is False:
            # Called before but not finished the replacement, this means there
            # is a circular dependency.
            raise CommandError(
                f"Cyclical squash replacement found, starting at {migration_key}"
            )
        self.replacements_progress[migration_key] = False
        migration = self.replacements[migration_key]
        # Process potential squashed migrations that the migration replaces.
        for replace_migration_key in migration.replaces:
            if replace_migration_key in self.replacements:
                self.replace_migration(replace_migration_key)

        replaced_keys = self._resolve_replaced_migration_keys(migration)
        # Get applied status of each found replacement target.
        applied_statuses = [
            (target in self.applied_migrations) for target in replaced_keys
        ]
        # The replacing migration is only marked as applied if all of its
        # replacement targets are applied.
        if all(applied_statuses):
            self.applied_migrations[migration_key] = migration
        else:
            self.applied_migrations.pop(migration_key, None)
        # A replacing migration can be used if either all or none of its
        # replacement targets have been applied.
        if all(applied_statuses) or (not any(applied_statuses)):
            self.graph.remove_replaced_nodes(migration_key, migration.replaces)
        else:
            # This replacing migration cannot be used because it is
            # partially applied. Remove it from the graph and remap
            # dependencies to it (#25945).
            self.graph.remove_replacement_node(migration_key, migration.replaces)

        self.replacements_progress[migration_key] = True
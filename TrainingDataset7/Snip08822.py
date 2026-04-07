def write_to_last_migration_files(self, changes):
        loader = MigrationLoader(connections[DEFAULT_DB_ALIAS])
        new_changes = {}
        update_previous_migration_paths = {}
        for app_label, app_migrations in changes.items():
            # Find last migration.
            leaf_migration_nodes = loader.graph.leaf_nodes(app=app_label)
            if len(leaf_migration_nodes) == 0:
                raise CommandError(
                    f"App {app_label} has no migration, cannot update last migration."
                )
            leaf_migration_node = leaf_migration_nodes[0]
            # Multiple leaf nodes have already been checked earlier in command.
            leaf_migration = loader.graph.nodes[leaf_migration_node]
            # Updated migration cannot be a squash migration, a dependency of
            # another migration, and cannot be already applied.
            if leaf_migration.replaces:
                raise CommandError(
                    f"Cannot update squash migration '{leaf_migration}'."
                )
            if leaf_migration_node in loader.applied_migrations:
                raise CommandError(
                    f"Cannot update applied migration '{leaf_migration}'."
                )
            depending_migrations = [
                migration
                for migration in loader.disk_migrations.values()
                if leaf_migration_node in migration.dependencies
            ]
            if depending_migrations:
                formatted_migrations = ", ".join(
                    [f"'{migration}'" for migration in depending_migrations]
                )
                raise CommandError(
                    f"Cannot update migration '{leaf_migration}' that migrations "
                    f"{formatted_migrations} depend on."
                )
            # Build new migration.
            for migration in app_migrations:
                leaf_migration.operations.extend(migration.operations)

                for dependency in migration.dependencies:
                    if isinstance(dependency, SwappableTuple):
                        if settings.AUTH_USER_MODEL == dependency.setting:
                            leaf_migration.dependencies.append(
                                ("__setting__", "AUTH_USER_MODEL")
                            )
                        else:
                            leaf_migration.dependencies.append(dependency)
                    elif dependency[0] != migration.app_label:
                        leaf_migration.dependencies.append(dependency)
            # Optimize migration.
            optimizer = MigrationOptimizer()
            leaf_migration.operations = optimizer.optimize(
                leaf_migration.operations, app_label
            )
            # Update name.
            previous_migration_path = MigrationWriter(leaf_migration).path
            name_fragment = self.migration_name or leaf_migration.suggest_name()
            suggested_name = leaf_migration.name[:4] + f"_{name_fragment}"
            if leaf_migration.name == suggested_name:
                new_name = leaf_migration.name + "_updated"
            else:
                new_name = suggested_name
            leaf_migration.name = new_name
            # Register overridden migration.
            new_changes[app_label] = [leaf_migration]
            update_previous_migration_paths[app_label] = previous_migration_path

        self.write_migration_files(new_changes, update_previous_migration_paths)
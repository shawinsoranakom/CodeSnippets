def show_list(self, connection, app_names=None):
        """
        Show a list of all migrations on the system, or only those of
        some named apps.
        """
        # Load migrations from disk/DB
        loader = MigrationLoader(connection, ignore_no_migrations=True)
        recorder = MigrationRecorder(connection)
        recorded_migrations = recorder.applied_migrations()
        graph = loader.graph
        # If we were passed a list of apps, validate it
        if app_names:
            self._validate_app_names(loader, app_names)
        # Otherwise, show all apps in alphabetic order
        else:
            app_names = sorted(loader.migrated_apps)
        # For each app, print its migrations in order from oldest (roots) to
        # newest (leaves).
        for app_name in app_names:
            self.stdout.write(app_name, self.style.MIGRATE_LABEL)
            shown = set()
            for node in graph.leaf_nodes(app_name):
                for plan_node in graph.forwards_plan(node):
                    if plan_node not in shown and plan_node[0] == app_name:
                        # Give it a nice title if it's a squashed one
                        title = plan_node[1]
                        if graph.nodes[plan_node].replaces:
                            title += " (%s squashed migrations)" % len(
                                graph.nodes[plan_node].replaces
                            )
                        applied_migration = loader.applied_migrations.get(plan_node)
                        # Mark it as applied/unapplied
                        if applied_migration:
                            if plan_node in recorded_migrations:
                                output = " [X] %s" % title
                            else:
                                title += " Run 'manage.py migrate' to finish recording."
                                output = " [-] %s" % title
                            if self.verbosity >= 2 and hasattr(
                                applied_migration, "applied"
                            ):
                                output += (
                                    " (applied at %s)"
                                    % applied_migration.applied.strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    )
                                )
                            self.stdout.write(output)
                        else:
                            self.stdout.write(" [ ] %s" % title)
                        shown.add(plan_node)
            # If we didn't print anything, then a small message
            if not shown:
                self.stdout.write(" (no migrations)", self.style.ERROR)
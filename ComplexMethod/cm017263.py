def _trim_to_apps(self, changes, app_labels):
        """
        Take changes from arrange_for_graph() and set of app labels, and return
        a modified set of changes which trims out as many migrations that are
        not in app_labels as possible. Note that some other migrations may
        still be present as they may be required dependencies.
        """
        # Gather other app dependencies in a first pass
        app_dependencies = {}
        for app_label, migrations in changes.items():
            for migration in migrations:
                for dep_app_label, name in migration.dependencies:
                    app_dependencies.setdefault(app_label, set()).add(dep_app_label)
        required_apps = set(app_labels)
        # Keep resolving till there's no change
        old_required_apps = None
        while old_required_apps != required_apps:
            old_required_apps = set(required_apps)
            required_apps.update(
                *[app_dependencies.get(app_label, ()) for app_label in required_apps]
            )
        # Remove all migrations that aren't needed
        for app_label in list(changes):
            if app_label not in required_apps:
                del changes[app_label]
        return changes
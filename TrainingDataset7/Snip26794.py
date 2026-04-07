def assertNumberMigrations(self, changes, app_label, number):
        if len(changes.get(app_label, [])) != number:
            self.fail(
                "Incorrect number of migrations (%s) for %s (expected %s)\n%s"
                % (
                    len(changes.get(app_label, [])),
                    app_label,
                    number,
                    self.repr_changes(changes),
                )
            )
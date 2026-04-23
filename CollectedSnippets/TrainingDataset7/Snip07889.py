def _check_postgres_installed(self, *args):
        # When subclassed by Index or BaseConstraint subclasses, args is
        # (model, connection).
        obj = args[0] if args else self
        if not apps.is_installed("django.contrib.postgres"):
            return [
                checks.Error(
                    "'django.contrib.postgres' must be in INSTALLED_APPS in "
                    "order to use %s." % self.__class__.__name__,
                    obj=obj,
                    id="postgres.E005",
                )
            ]
        return []
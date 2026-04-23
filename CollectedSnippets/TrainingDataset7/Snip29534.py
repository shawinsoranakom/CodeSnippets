def _make_error(self, obj, klass_name):
        """Helper to create postgres.E005 error for specific objects."""
        return checks.Error(
            "'django.contrib.postgres' must be in INSTALLED_APPS in order to "
            f"use {klass_name}.",
            obj=obj,
            id="postgres.E005",
        )
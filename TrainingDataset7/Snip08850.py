def get_auto_imports(self):
        """Return a sequence of import paths for objects to be auto-imported.

        By default, import paths for models in INSTALLED_APPS and some common
        utilities are included, with models from earlier apps taking precedence
        in case of a name collision.

        For example, for an unchanged INSTALLED_APPS, this method returns:

        [
            "django.conf.settings",
            "django.db.connection",
            "django.db.models",
            "django.db.models.functions",
            "django.db.reset_queries",
            "django.utils.timezone",
            "django.contrib.sessions.models.Session",
            "django.contrib.contenttypes.models.ContentType",
            "django.contrib.auth.models.User",
            "django.contrib.auth.models.Group",
            "django.contrib.auth.models.Permission",
            "django.contrib.admin.models.LogEntry",
        ]

        """
        default_imports = [
            "django.conf.settings",
            "django.db.connection",
            "django.db.models",
            "django.db.models.functions",
            "django.db.reset_queries",
            "django.utils.timezone",
        ]
        app_models_imports = default_imports + [
            f"{model.__module__}.{model.__name__}"
            for model in reversed(apps.get_models())
            if model.__module__
        ]
        return app_models_imports
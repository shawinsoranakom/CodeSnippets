def check(self, app_configs):
        """
        Run the system checks on all ModelAdmins, except if they aren't
        customized at all.
        """
        if app_configs is None:
            app_configs = apps.get_app_configs()
        app_configs = set(app_configs)  # Speed up lookups below

        errors = []
        modeladmins = (
            o for o in self._registry.values() if o.__class__ is not ModelAdmin
        )
        for modeladmin in modeladmins:
            if modeladmin.model._meta.app_config in app_configs:
                errors.extend(modeladmin.check())
        return errors
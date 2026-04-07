def get_paths(self, packages):
        allowable_packages = {
            app_config.name: app_config for app_config in apps.get_app_configs()
        }
        app_configs = [
            allowable_packages[p] for p in packages if p in allowable_packages
        ]
        if len(app_configs) < len(packages):
            excluded = [p for p in packages if p not in allowable_packages]
            raise ValueError(
                "Invalid package(s) provided to JavaScriptCatalog: %s"
                % ",".join(excluded)
            )
        # paths of requested packages
        return [os.path.join(app.path, "locale") for app in app_configs]
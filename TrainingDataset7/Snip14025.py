def enable(self):
        self.old_apps = Options.default_apps
        apps = Apps(self.installed_apps)
        setattr(Options, "default_apps", apps)
        return apps
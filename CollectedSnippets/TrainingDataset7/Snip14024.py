def __init__(self, *installed_apps, **kwargs):
        self.installed_apps = installed_apps
        super().__init__(**kwargs)
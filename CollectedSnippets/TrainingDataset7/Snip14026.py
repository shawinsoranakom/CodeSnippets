def disable(self):
        setattr(Options, "default_apps", self.old_apps)
def __getattr__(self, name):
        if name == "FOO":
            return "bar"
        return getattr(global_settings, name)
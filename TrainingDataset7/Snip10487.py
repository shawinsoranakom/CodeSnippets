def __init__(self, models=None, real_apps=None):
        self.models = models or {}
        # Apps to include from main registry, usually unmigrated ones
        if real_apps is None:
            real_apps = set()
        else:
            assert isinstance(real_apps, set)
        self.real_apps = real_apps
        self.is_delayed = False
        # {remote_model_key: {model_key: {field_name: field}}}
        self._relations = None
def __init__(self, params):
        """
        Initialize the template engine.

        `params` is a dict of configuration settings.
        """
        params = params.copy()
        self.name = params.pop("NAME")
        self.dirs = list(params.pop("DIRS"))
        self.app_dirs = params.pop("APP_DIRS")
        if params:
            raise ImproperlyConfigured(
                "Unknown parameters: {}".format(", ".join(params))
            )
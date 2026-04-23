def __init__(
        self,
        dirs=None,
        app_dirs=False,
        context_processors=None,
        debug=False,
        loaders=None,
        string_if_invalid="",
        file_charset="utf-8",
        libraries=None,
        builtins=None,
        autoescape=True,
    ):
        if dirs is None:
            dirs = []
        if context_processors is None:
            context_processors = []
        if loaders is None:
            loaders = ["django.template.loaders.filesystem.Loader"]
            if app_dirs:
                loaders += ["django.template.loaders.app_directories.Loader"]
            loaders = [("django.template.loaders.cached.Loader", loaders)]
        else:
            if app_dirs:
                raise ImproperlyConfigured(
                    "app_dirs must not be set when loaders is defined."
                )
        if libraries is None:
            libraries = {}
        if builtins is None:
            builtins = []

        self.dirs = dirs
        self.app_dirs = app_dirs
        self.autoescape = autoescape
        self.context_processors = context_processors
        self.debug = debug
        self.loaders = loaders
        self.string_if_invalid = string_if_invalid
        self.file_charset = file_charset
        self.libraries = libraries
        self.template_libraries = self.get_template_libraries(libraries)
        self.builtins = self.default_builtins + builtins
        self.template_builtins = self.get_template_builtins(self.builtins)
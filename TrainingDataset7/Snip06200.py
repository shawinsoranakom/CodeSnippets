def _load_library(self):
        if self.library is not None:
            if isinstance(self.library, (tuple, list)):
                name, mod_path = self.library
            else:
                mod_path = self.library
            try:
                module = importlib.import_module(mod_path)
            except ImportError as e:
                raise ValueError(
                    "Couldn't load %r algorithm library: %s"
                    % (self.__class__.__name__, e)
                )
            return module
        raise ValueError(
            "Hasher %r doesn't specify a library attribute" % self.__class__.__name__
        )
def _init_translation_catalog(self):
        """Create a base catalog using global django translations."""
        settingsfile = sys.modules[settings.__module__].__file__
        localedir = os.path.join(os.path.dirname(settingsfile), "locale")
        translation = self._new_gnu_trans(localedir)
        self.merge(translation)
def __getitem__(self, name):
        """Return a Media object that only contains media of the given type."""
        if name in MEDIA_TYPES:
            return Media(**{str(name): getattr(self, "_" + name)})
        raise KeyError('Unknown media type "%s"' % name)
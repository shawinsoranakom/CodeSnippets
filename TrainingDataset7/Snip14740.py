def merge(self, other):
        """Merge another translation into this catalog."""
        if not getattr(other, "_catalog", None):
            return  # NullTranslations() has no _catalog
        if self._catalog is None:
            # Take plural and _info from first catalog found (generally
            # Django's).
            self.plural = other.plural
            self._info = other._info.copy()
            self._catalog = TranslationCatalog(other)
        else:
            self._catalog.update(other)
        if other._fallback:
            self.add_fallback(other._fallback)
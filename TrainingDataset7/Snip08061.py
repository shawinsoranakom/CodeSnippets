def _location(self, item, force_lang_code=None):
        if self.i18n:
            obj, lang_code = item
            # Activate language from item-tuple or forced one before calling
            # location.
            with translation.override(force_lang_code or lang_code):
                return self._get("location", item)
        return self._get("location", item)
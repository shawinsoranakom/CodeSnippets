def _add_fallback(self, localedirs=None):
        """Set the GNUTranslations() fallback with the default language."""
        # Don't set a fallback for the default language or any English variant
        # (as it's empty, so it'll ALWAYS fall back to the default language)
        if self.__language == settings.LANGUAGE_CODE or self.__language.startswith(
            "en"
        ):
            return
        if self.domain == "django":
            # Get from cache
            default_translation = translation(settings.LANGUAGE_CODE)
        else:
            default_translation = DjangoTranslation(
                settings.LANGUAGE_CODE, domain=self.domain, localedirs=localedirs
            )
        self.add_fallback(default_translation)
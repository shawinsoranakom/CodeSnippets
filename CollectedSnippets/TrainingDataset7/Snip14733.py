def __init__(self, language, domain=None, localedirs=None):
        """Create a GNUTranslations() using many locale directories"""
        gettext_module.GNUTranslations.__init__(self)
        if domain is not None:
            self.domain = domain

        self.__language = language
        self.__to_language = to_language(language)
        self.__locale = to_locale(language)
        self._catalog = None
        # If a language doesn't have a catalog, use the Germanic default for
        # pluralization: anything except one is pluralized.
        self.plural = lambda n: int(n != 1)

        if self.domain == "django":
            if localedirs is not None:
                # A module-level cache is used for caching 'django'
                # translations
                warnings.warn(
                    "localedirs is ignored when domain is 'django'.", RuntimeWarning
                )
                localedirs = None
            self._init_translation_catalog()

        if localedirs:
            for localedir in localedirs:
                translation = self._new_gnu_trans(localedir)
                self.merge(translation)
        else:
            self._add_installed_apps_translations()

        self._add_local_translations()
        if (
            self.__language == settings.LANGUAGE_CODE
            and self.domain == "django"
            and self._catalog is None
        ):
            # default lang should have at least one translation file available.
            raise OSError(
                "No translation files found for default language %s."
                % settings.LANGUAGE_CODE
            )
        self._add_fallback(localedirs)
        if self._catalog is None:
            # No catalogs found for this language, set an empty catalog.
            self._catalog = TranslationCatalog()
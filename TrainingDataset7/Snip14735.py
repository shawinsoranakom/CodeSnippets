def _new_gnu_trans(self, localedir, use_null_fallback=True):
        """
        Return a mergeable gettext.GNUTranslations instance.

        A convenience wrapper. By default gettext uses 'fallback=False'.
        Using param `use_null_fallback` to avoid confusion with any other
        references to 'fallback'.
        """
        return gettext_module.translation(
            domain=self.domain,
            localedir=localedir,
            languages=[self.__locale],
            fallback=use_null_fallback,
        )
def test_sub_locales(self):
        """
        Check if sublocales fall back to the main locale
        """
        with self.settings(USE_THOUSAND_SEPARATOR=True):
            with translation.override("de-at", deactivate=True):
                self.assertEqual("66.666,666", Template("{{ n }}").render(self.ctxt))
            with translation.override("es-us", deactivate=True):
                self.assertEqual("31 de diciembre de 2009", date_format(self.d))
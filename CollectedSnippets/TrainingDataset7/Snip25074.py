def test_maclines(self):
        """
        Translations on files with Mac or DOS end of lines will be converted
        to unix EOF in .po catalogs.
        """
        ca_translation = trans_real.translation("ca")
        ca_translation._catalog["Mac\nEOF\n"] = "Catalan Mac\nEOF\n"
        ca_translation._catalog["Win\nEOF\n"] = "Catalan Win\nEOF\n"
        with translation.override("ca", deactivate=True):
            self.assertEqual("Catalan Mac\nEOF\n", gettext("Mac\rEOF\r"))
            self.assertEqual("Catalan Win\nEOF\n", gettext("Win\r\nEOF\r\n"))
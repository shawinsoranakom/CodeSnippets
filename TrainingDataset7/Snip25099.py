def test_iter_format_modules_stability(self):
        """
        Tests the iter_format_modules function always yields format modules in
        a stable and correct order in presence of both base ll and ll_CC
        formats.
        """
        en_format_mod = import_module("django.conf.locale.en.formats")
        en_gb_format_mod = import_module("django.conf.locale.en_GB.formats")
        self.assertEqual(
            list(iter_format_modules("en-gb")), [en_gb_format_mod, en_format_mod]
        )
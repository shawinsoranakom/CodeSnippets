def test_media(self):
        rel = Album._meta.get_field("band").remote_field
        base_files = (
            "admin/js/vendor/jquery/jquery.min.js",
            "admin/js/vendor/select2/select2.full.min.js",
            # Language file is inserted here.
            "admin/js/jquery.init.js",
            "admin/js/autocomplete.js",
        )
        languages = (
            ("de", "de"),
            # Subsequent language codes are used when the language code is not
            # supported.
            ("de-at", "de"),
            ("de-ch-1901", "de"),
            ("en-latn-us", "en"),
            ("nl-nl-x-informal", "nl"),
            ("zh-hans-HK", "zh-CN"),
            # Language with code 00 does not exist.
            ("00", None),
            # Language files are case sensitive.
            ("sr-cyrl", "sr-Cyrl"),
            ("zh-hans", "zh-CN"),
            ("zh-hant", "zh-TW"),
            (None, None),
        )
        for lang, select_lang in languages:
            with self.subTest(lang=lang):
                if select_lang:
                    expected_files = (
                        base_files[:2]
                        + (("admin/js/vendor/select2/i18n/%s.js" % select_lang),)
                        + base_files[2:]
                    )
                else:
                    expected_files = base_files
                with translation.override(lang):
                    self.assertEqual(
                        AutocompleteSelect(rel, admin.site).media._js,
                        list(expected_files),
                    )
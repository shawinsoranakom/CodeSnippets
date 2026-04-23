def test_multiple_plurals_merge(self):
        def _create_translation_from_string(content):
            with tempfile.TemporaryDirectory() as dirname:
                po_path = Path(dirname).joinpath("fr", "LC_MESSAGES", "django.po")
                po_path.parent.mkdir(parents=True)
                po_path.write_text(content)
                errors = popen_wrapper(
                    ["msgfmt", "-o", po_path.with_suffix(".mo"), po_path]
                )[1]
                if errors:
                    self.fail(f"msgfmt compilation error: {errors}")
                return gettext_module.translation(
                    domain="django",
                    localedir=dirname,
                    languages=["fr"],
                )

        french = trans_real.catalog()
        # Merge a new translation file with different plural forms.
        catalog1 = _create_translation_from_string(
            'msgid ""\n'
            'msgstr ""\n'
            '"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '"Plural-Forms: nplurals=3; plural=(n==1 ? 0 : n==0 ? 1 : 2);\\n"\n'
            'msgid "I win"\n'
            'msgstr "Je perds"\n'
        )
        french.merge(catalog1)
        # Merge a second translation file with plural forms from django.conf.
        catalog2 = _create_translation_from_string(
            'msgid ""\n'
            'msgstr ""\n'
            '"Content-Type: text/plain; charset=UTF-8\\n"\n'
            '"Plural-Forms: Plural-Forms: nplurals=2; plural=(n > 1);\\n"\n'
            'msgid "I win"\n'
            'msgstr "Je gagne"\n'
        )
        french.merge(catalog2)
        # Translations from this last one are supposed to win.
        self.assertEqual(french.gettext("I win"), "Je gagne")
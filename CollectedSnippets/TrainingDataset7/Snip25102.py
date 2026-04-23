def test_localize_templatetag_and_filter(self):
        """
        Test the {% localize %} templatetag and the localize/unlocalize
        filters.
        """
        context = Context(
            {"int": 1455, "float": 3.14, "date": datetime.date(2016, 12, 31)}
        )
        template1 = Template(
            "{% load l10n %}{% localize %}"
            "{{ int }}/{{ float }}/{{ date }}{% endlocalize %}; "
            "{% localize on %}{{ int }}/{{ float }}/{{ date }}{% endlocalize %}"
        )
        template2 = Template(
            "{% load l10n %}{{ int }}/{{ float }}/{{ date }}; "
            "{% localize off %}{{ int }}/{{ float }}/{{ date }};{% endlocalize %} "
            "{{ int }}/{{ float }}/{{ date }}"
        )
        template3 = Template(
            "{% load l10n %}{{ int }}/{{ float }}/{{ date }}; "
            "{{ int|unlocalize }}/{{ float|unlocalize }}/{{ date|unlocalize }}"
        )
        expected_localized = "1.455/3,14/31. Dezember 2016"
        expected_unlocalized = "1455/3.14/Dez. 31, 2016"
        output1 = "; ".join([expected_localized, expected_localized])
        output2 = "; ".join(
            [expected_localized, expected_unlocalized, expected_localized]
        )
        output3 = "; ".join([expected_localized, expected_unlocalized])
        with translation.override("de", deactivate=True):
            with self.settings(USE_THOUSAND_SEPARATOR=True):
                self.assertEqual(template1.render(context), output1)
                self.assertEqual(template2.render(context), output2)
                self.assertEqual(template3.render(context), output3)
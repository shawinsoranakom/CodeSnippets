def test_localized_off_numbers(self):
        """A string representation is returned for unlocalized numbers."""
        template = Template(
            "{% load l10n %}{% localize off %}"
            "{{ int }}/{{ float }}/{{ decimal }}{% endlocalize %}"
        )
        context = Context(
            {"int": 1455, "float": 3.14, "decimal": decimal.Decimal("24.1567")}
        )
        with self.settings(
            DECIMAL_SEPARATOR=",",
            USE_THOUSAND_SEPARATOR=True,
            THOUSAND_SEPARATOR="°",
            NUMBER_GROUPING=2,
        ):
            self.assertEqual(template.render(context), "1455/3.14/24.1567")
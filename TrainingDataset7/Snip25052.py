def test_translates_with_percent_symbol_in_the_middle(self):
        expected = "Pour cent littérale % avec un symbole au milieu"

        trans_tpl = Template(
            "{% load i18n %}"
            '{% translate "Literal with a percent % symbol in the middle" %}'
        )
        self.assertEqual(trans_tpl.render(Context({})), expected)

        block_tpl = Template(
            "{% load i18n %}{% blocktranslate %}Literal with a percent % symbol "
            "in the middle{% endblocktranslate %}"
        )
        self.assertEqual(block_tpl.render(Context({})), expected)
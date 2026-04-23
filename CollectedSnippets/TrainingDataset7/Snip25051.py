def test_translates_with_a_percent_symbol_at_the_end(self):
        expected = "Littérale avec un symbole de pour cent à la fin %"

        trans_tpl = Template(
            "{% load i18n %}"
            '{% translate "Literal with a percent symbol at the end %" %}'
        )
        self.assertEqual(trans_tpl.render(Context({})), expected)

        block_tpl = Template(
            "{% load i18n %}{% blocktranslate %}Literal with a percent symbol at "
            "the end %{% endblocktranslate %}"
        )
        self.assertEqual(block_tpl.render(Context({})), expected)
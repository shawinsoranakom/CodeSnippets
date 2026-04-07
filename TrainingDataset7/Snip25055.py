def test_translates_multiple_percent_signs(self):
        expected = (
            "1 % signe pour cent, signes %% 2 pour cent, trois signes de pourcentage "
            "%%%"
        )
        trans_tpl = Template(
            '{% load i18n %}{% translate "1 percent sign %, 2 percent signs %%, '
            '3 percent signs %%%" %}'
        )
        self.assertEqual(trans_tpl.render(Context({})), expected)
        block_tpl = Template(
            "{% load i18n %}{% blocktranslate %}1 percent sign %, 2 percent signs "
            "%%, 3 percent signs %%%{% endblocktranslate %}"
        )
        self.assertEqual(block_tpl.render(Context({})), expected)

        block_tpl = Template(
            "{% load i18n %}{% blocktranslate %}{{name}} says: 1 percent sign %, "
            "2 percent signs %%{% endblocktranslate %}"
        )
        self.assertEqual(
            block_tpl.render(Context({"name": "Django"})),
            "Django dit: 1 pour cent signe %, deux signes de pourcentage %%",
        )
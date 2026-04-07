def test_translates_with_percent_symbol_using_context(self):
        trans_tpl = Template('{% load i18n %}{% translate "It is 100%" %}')
        self.assertEqual(trans_tpl.render(Context({})), "Il est de 100%")
        trans_tpl = Template(
            '{% load i18n %}{% translate "It is 100%" context "female" %}'
        )
        self.assertEqual(trans_tpl.render(Context({})), "Elle est de 100%")

        block_tpl = Template(
            "{% load i18n %}{% blocktranslate %}It is 100%{% endblocktranslate %}"
        )
        self.assertEqual(block_tpl.render(Context({})), "Il est de 100%")
        block_tpl = Template(
            "{% load i18n %}"
            '{% blocktranslate context "female" %}It is 100%{% endblocktranslate %}'
        )
        self.assertEqual(block_tpl.render(Context({})), "Elle est de 100%")
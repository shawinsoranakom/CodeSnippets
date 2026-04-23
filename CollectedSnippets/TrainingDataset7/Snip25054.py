def test_translates_with_string_that_look_like_fmt_spec_with_trans(self):
        # tests "%s"
        expected = (
            "On dirait un spec str fmt %s mais ne devrait pas être interprété comme "
            "plus disponible"
        )
        trans_tpl = Template(
            '{% load i18n %}{% translate "Looks like a str fmt spec %s but '
            'should not be interpreted as such" %}'
        )
        self.assertEqual(trans_tpl.render(Context({})), expected)
        block_tpl = Template(
            "{% load i18n %}{% blocktranslate %}Looks like a str fmt spec %s but "
            "should not be interpreted as such{% endblocktranslate %}"
        )
        self.assertEqual(block_tpl.render(Context({})), expected)

        # tests "% o"
        expected = (
            "On dirait un spec str fmt % o mais ne devrait pas être interprété comme "
            "plus disponible"
        )
        trans_tpl = Template(
            "{% load i18n %}"
            '{% translate "Looks like a str fmt spec % o but should not be '
            'interpreted as such" %}'
        )
        self.assertEqual(trans_tpl.render(Context({})), expected)
        block_tpl = Template(
            "{% load i18n %}"
            "{% blocktranslate %}Looks like a str fmt spec % o but should not be "
            "interpreted as such{% endblocktranslate %}"
        )
        self.assertEqual(block_tpl.render(Context({})), expected)
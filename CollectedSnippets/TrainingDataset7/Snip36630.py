def assertRenderEqual(self, tpl, expected, **context):
        context = Context(context)
        tpl = Template(tpl)
        self.assertEqual(tpl.render(context), expected)
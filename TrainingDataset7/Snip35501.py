def test_localtime_templatetag_invalid_argument(self):
        with self.assertRaises(TemplateSyntaxError):
            Template("{% load tz %}{% localtime foo %}{% endlocaltime %}").render()
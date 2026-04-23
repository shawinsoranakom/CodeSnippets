def test_ifchanged_render_once(self):
        """
        #19890. The content of ifchanged template tag was rendered twice.
        """
        template = self.engine.from_string(
            '{% ifchanged %}{% cycle "1st time" "2nd time" %}{% endifchanged %}'
        )
        output = template.render(Context({}))
        self.assertEqual(output, "1st time")
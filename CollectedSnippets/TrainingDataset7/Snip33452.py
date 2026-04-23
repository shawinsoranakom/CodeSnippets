def test_unknown_source_template(self):
        try:
            Template("{% endfor %}")
        except TemplateSyntaxError as e:
            self.assertEqual(str(e), self.template_error_msg)
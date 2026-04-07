def test_template_name_in_error_message(self):
        msg = f"Template: test.html, {self.template_error_msg}"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            Template("{% endfor %}", origin=Origin("test.html"))
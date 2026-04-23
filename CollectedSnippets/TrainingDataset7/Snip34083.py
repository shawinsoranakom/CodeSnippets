def test_with_error01(self):
        with self.assertRaisesMessage(TemplateSyntaxError, self.at_least_with_one_msg):
            self.engine.render_to_string("with-error01", {"dict": {"key": 50}})
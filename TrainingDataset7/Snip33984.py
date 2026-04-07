def test_static_statictag_without_path(self):
        msg = "'static' takes at least one argument (path to file)"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("t")
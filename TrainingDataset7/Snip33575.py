def test_extends_duplicate(self):
        msg = "'extends' cannot appear more than once in the same template"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("extends_duplicate")
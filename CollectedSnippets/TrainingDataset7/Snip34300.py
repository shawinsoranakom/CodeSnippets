def test_extends_not_first_tag_in_extended_template(self):
        msg = "{% extends 'base.html' %} must be the first tag in 'index.html'."
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("index.html")
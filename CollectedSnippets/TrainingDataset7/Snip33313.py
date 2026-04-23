def test_plural_bad_syntax(self, tag_name):
        msg = "'{}' doesn't allow other block tags inside it".format(tag_name)
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template", {"var": [1, 2, 3]})
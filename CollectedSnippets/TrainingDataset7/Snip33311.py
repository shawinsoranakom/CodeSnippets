def test_count(self, tag_name):
        msg = "\"count\" in '{}' tag expected exactly one keyword argument.".format(
            tag_name
        )
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template", {"a": [1, 2, 3]})
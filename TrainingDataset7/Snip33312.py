def test_count_not_number(self, tag_name):
        msg = "'counter' argument to '{}' tag must be a number.".format(tag_name)
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.render_to_string("template", {"num": "1"})
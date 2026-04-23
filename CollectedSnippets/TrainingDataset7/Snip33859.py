def test_load07(self):
        msg = "'bad_tag' is not a valid tag or filter in tag library 'testtags'"
        with self.assertRaisesMessage(TemplateSyntaxError, msg):
            self.engine.get_template("load07")
def test_querystring_same_arg(self):
        msg = "'querystring' received multiple values for keyword argument 'a'"
        self.assertTemplateSyntaxError("querystring_same_arg", {}, msg)
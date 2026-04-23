def test_no_value(self):
        """
        If insufficient data is provided, None is substituted.
        """
        msg = "'This field is required.'"
        with self.assertRaisesMessage(ValidationError, msg):
            self.field.clean(["some text", ["JP"]])
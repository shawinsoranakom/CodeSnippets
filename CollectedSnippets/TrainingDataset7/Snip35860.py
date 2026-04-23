def test_non_string_value(self):
        msg = "'1' is not a callable or a dot-notation path"
        with self.assertRaisesMessage(ViewDoesNotExist, msg):
            get_callable(1)
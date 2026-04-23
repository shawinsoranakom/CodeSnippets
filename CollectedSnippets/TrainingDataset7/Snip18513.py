def test_no_limit_value(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "no_limit_value"
        ):
            self.ops.no_limit_value()
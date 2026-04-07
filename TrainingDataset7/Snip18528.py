def test_format_for_duration_arithmetic(self):
        msg = self.may_require_msg % "format_for_duration_arithmetic"
        with self.assertRaisesMessage(NotImplementedError, msg):
            self.ops.format_for_duration_arithmetic(None)
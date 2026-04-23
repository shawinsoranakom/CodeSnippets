def test_quote_name(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "quote_name"
        ):
            self.ops.quote_name("a")
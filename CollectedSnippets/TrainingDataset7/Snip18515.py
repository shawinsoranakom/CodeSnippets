def test_regex_lookup(self):
        with self.assertRaisesMessage(
            NotImplementedError, self.may_require_msg % "regex_lookup"
        ):
            self.ops.regex_lookup(lookup_type="regex")
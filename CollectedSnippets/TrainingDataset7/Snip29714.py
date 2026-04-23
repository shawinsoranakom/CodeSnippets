def test_empty_expressions(self):
        msg = "At least one expression is required to define an exclusion constraint."
        for empty_expressions in (None, []):
            with (
                self.subTest(empty_expressions),
                self.assertRaisesMessage(ValueError, msg),
            ):
                ExclusionConstraint(
                    index_type="GIST",
                    name="exclude_empty_expressions",
                    expressions=empty_expressions,
                )
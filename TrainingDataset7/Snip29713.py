def test_invalid_expressions(self):
        msg = "The expressions must be a list of 2-tuples."
        for expressions in (["foo"], [("foo",)], [("foo_1", "foo_2", "foo_3")]):
            with self.subTest(expressions), self.assertRaisesMessage(ValueError, msg):
                ExclusionConstraint(
                    index_type="GIST",
                    name="exclude_invalid_expressions",
                    expressions=expressions,
                )
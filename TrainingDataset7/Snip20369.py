def test_null_literal(self):
        msg = "Oracle does not allow Value(None) for expression1."
        with self.assertRaisesMessage(ValueError, msg):
            list(
                Author.objects.annotate(nullif=NullIf(Value(None), "name")).values_list(
                    "nullif"
                )
            )
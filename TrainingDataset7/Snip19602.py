def test_rhs_combinable(self):
        msg = "CombinedExpression expression does not support composite primary keys."
        for expr in [F("pk") + (1, 1), (1, 1) + F("pk")]:
            with (
                self.subTest(expression=expr),
                self.assertRaisesMessage(ValueError, msg),
            ):
                Comment.objects.filter(text__gt=expr).count()
def test_operator_on_combined_qs_error(self):
        qs = Number.objects.all()
        msg = "Cannot use %s operator with combined queryset."
        combinators = ["union"]
        if connection.features.supports_select_difference:
            combinators.append("difference")
        if connection.features.supports_select_intersection:
            combinators.append("intersection")
        operators = [
            ("|", operator.or_),
            ("&", operator.and_),
            ("^", operator.xor),
        ]
        for combinator in combinators:
            combined_qs = getattr(qs, combinator)(qs)
            for operator_, operator_func in operators:
                with self.subTest(combinator=combinator):
                    with self.assertRaisesMessage(TypeError, msg % operator_):
                        operator_func(qs, combined_qs)
                    with self.assertRaisesMessage(TypeError, msg % operator_):
                        operator_func(combined_qs, qs)
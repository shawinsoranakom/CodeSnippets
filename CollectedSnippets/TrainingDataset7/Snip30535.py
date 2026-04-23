def test_get_with_filters_unsupported_on_combined_qs(self):
        qs = Number.objects.all()
        msg = "Calling QuerySet.get(...) with filters after %s() is not supported."
        combinators = ["union"]
        if connection.features.supports_select_difference:
            combinators.append("difference")
        if connection.features.supports_select_intersection:
            combinators.append("intersection")
        for combinator in combinators:
            with self.subTest(combinator=combinator):
                with self.assertRaisesMessage(NotSupportedError, msg % combinator):
                    getattr(qs, combinator)(qs).get(num=2)
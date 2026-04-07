def test_unsupported_operations_on_combined_qs(self):
        qs = Number.objects.all()
        msg = "Calling QuerySet.%s() after %s() is not supported."
        combinators = ["union"]
        if connection.features.supports_select_difference:
            combinators.append("difference")
        if connection.features.supports_select_intersection:
            combinators.append("intersection")
        for combinator in combinators:
            for operation in (
                "alias",
                "annotate",
                "defer",
                "delete",
                "distinct",
                "exclude",
                "extra",
                "filter",
                "only",
                "prefetch_related",
                "select_related",
                "update",
            ):
                with self.subTest(combinator=combinator, operation=operation):
                    with self.assertRaisesMessage(
                        NotSupportedError,
                        msg % (operation, combinator),
                    ):
                        getattr(getattr(qs, combinator)(qs), operation)()
            with self.assertRaisesMessage(
                NotSupportedError,
                msg % ("contains", combinator),
            ):
                obj = Number.objects.first()
                getattr(qs, combinator)(qs).contains(obj)
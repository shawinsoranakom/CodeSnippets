def test_outer_ref_pk_filter_on_pk_comparison_unsupported(self):
        subquery = Subquery(User.objects.filter(pk=OuterRef("pk")).values("pk")[:1])
        tests = ["gt", "gte", "lt", "lte"]
        for lookup in tests:
            with self.subTest(f"pk__{lookup}"):
                qs = Comment.objects.filter(**{f"pk__{lookup}": subquery})
                with self.assertRaisesMessage(
                    NotSupportedError,
                    f'"{lookup}" cannot be used to target composite fields '
                    "through subqueries on this backend",
                ):
                    qs.count()
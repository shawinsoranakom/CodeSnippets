def test_relabeled_clone_rhs(self):
        Number.objects.bulk_create([Number(integer=1), Number(integer=2)])
        self.assertIs(
            Number.objects.filter(
                # Ensure iterable of expressions are properly re-labelled on
                # subquery pushdown. If the inner query __range right-hand-side
                # members are not relabelled they will point at the outer query
                # alias and this test will fail.
                Exists(
                    Number.objects.exclude(pk=OuterRef("pk")).filter(
                        integer__range=(F("integer"), F("integer"))
                    )
                )
            ).exists(),
            True,
        )
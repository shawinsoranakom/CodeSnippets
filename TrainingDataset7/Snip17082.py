def test_sliced_conditional_aggregate(self):
        self.assertEqual(
            Author.objects.order_by("pk")[:5].aggregate(
                test=Sum(Case(When(age__lte=35, then=1)))
            )["test"],
            3,
        )
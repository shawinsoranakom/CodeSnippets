def test_none_call_before_aggregate(self):
        # Regression for #11789
        self.assertEqual(
            Author.objects.none().aggregate(Avg("age")), {"age__avg": None}
        )
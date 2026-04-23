def test_count_distinct_not_supported(self):
        with self.assertRaisesMessage(
            ValueError, "COUNT(DISTINCT) doesn't support composite primary keys"
        ):
            self.assertIsNone(
                User.objects.annotate(comments__count=Count("comments", distinct=True))
            )
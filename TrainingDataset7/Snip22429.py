def test_query_does_not_mutate(self):
        """
        Recompiling the same subquery doesn't mutate it.
        """
        queryset = Friendship.objects.filter(to_friend__in=Person.objects.all())
        self.assertEqual(str(queryset.query), str(queryset.query))
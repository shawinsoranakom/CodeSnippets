def test_filter_query_does_not_mutate(self):
        queryset = User.objects.filter(comments__in=Comment.objects.all())
        self.assertEqual(str(queryset.query), str(queryset.query))
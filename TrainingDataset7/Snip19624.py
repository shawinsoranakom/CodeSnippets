def test_filter_users_by_comments_subquery(self):
        subquery = Comment.objects.filter(id=3).only("pk")
        queryset = User.objects.filter(comments__in=subquery)
        self.assertSequenceEqual(queryset, (self.user_2,))
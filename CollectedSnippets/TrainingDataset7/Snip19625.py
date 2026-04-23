def test_filter_comments_by_users_subquery(self):
        subquery = Comment.objects.filter(id=3).values("user")
        queryset = Comment.objects.filter(user__in=subquery)
        self.assertSequenceEqual(queryset, (self.comment_3,))
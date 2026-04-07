def test_explicit_subquery(self):
        subquery = Subquery(User.objects.values("pk"))
        self.assertEqual(User.objects.filter(pk__in=subquery).count(), 4)
        self.assertEqual(Comment.objects.filter(user__in=subquery).count(), 5)
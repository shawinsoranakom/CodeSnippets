def test_exact_sliced_queryset_not_limited_to_one(self):
        msg = (
            "The QuerySet value for an exact lookup must be limited to one "
            "result using slicing."
        )
        with self.assertRaisesMessage(ValueError, msg):
            list(Article.objects.filter(author=Author.objects.all()[:2]))
        with self.assertRaisesMessage(ValueError, msg):
            list(Article.objects.filter(author=Author.objects.all()[1:]))
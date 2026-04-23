def test_invalid_queryset_model(self):
        msg = 'Cannot use QuerySet for "Article": Use a QuerySet for "ExtraInfo".'
        with self.assertRaisesMessage(ValueError, msg):
            list(Author.objects.filter(extra=Article.objects.all()))
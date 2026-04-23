def test_annotate_exists(self):
        authors = Author.objects.annotate(c=Count("id")).filter(c__gt=1)
        self.assertFalse(authors.exists())
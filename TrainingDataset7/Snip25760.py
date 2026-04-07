def test_exists(self):
        # We can use .exists() to check that there are some
        self.assertTrue(Article.objects.exists())
        for a in Article.objects.all():
            a.delete()
        # There should be none now!
        self.assertFalse(Article.objects.exists())
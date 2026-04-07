def check():
            # We know that we've broken the __iter__ method, so the queryset
            # should always raise an exception.
            with self.assertRaises(IndexError):
                IndexErrorArticle.objects.all()[:10:2]
            with self.assertRaises(IndexError):
                IndexErrorArticle.objects.first()
            with self.assertRaises(IndexError):
                IndexErrorArticle.objects.last()
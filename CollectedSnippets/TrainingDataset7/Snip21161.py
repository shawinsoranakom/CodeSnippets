def test_large_deletes(self):
        """
        If the number of objects > chunk size, deletion still occurs.
        """
        for x in range(300):
            Book.objects.create(pagecount=x + 100)
        # attach a signal to make sure we will not fast-delete

        def noop(*args, **kwargs):
            pass

        models.signals.post_delete.connect(noop, sender=Book)
        Book.objects.all().delete()
        models.signals.post_delete.disconnect(noop, sender=Book)
        self.assertEqual(Book.objects.count(), 0)
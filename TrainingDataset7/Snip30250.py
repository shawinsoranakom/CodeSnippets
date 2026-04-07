def test_remove_clears_prefetched_objects(self):
        bookwithyear = BookWithYear.objects.get(pk=self.bookwithyear1.pk)
        prefetch_related_objects([bookwithyear], "bookreview_set")
        self.assertCountEqual(bookwithyear.bookreview_set.all(), [self.bookreview1])
        bookwithyear.bookreview_set.remove(self.bookreview1)
        self.assertCountEqual(bookwithyear.bookreview_set.all(), [])
def test_add_clears_prefetched_objects(self):
        bookwithyear = BookWithYear.objects.get(pk=self.bookwithyear1.pk)
        prefetch_related_objects([bookwithyear], "bookreview_set")
        self.assertCountEqual(bookwithyear.bookreview_set.all(), [self.bookreview1])
        new_review = BookReview.objects.create()
        bookwithyear.bookreview_set.add(new_review)
        self.assertCountEqual(
            bookwithyear.bookreview_set.all(), [self.bookreview1, new_review]
        )
def test_prefetch_reverse_foreign_key(self):
        with self.assertNumQueries(2):
            (bookwithyear1,) = BookWithYear.objects.prefetch_related("bookreview_set")
        with self.assertNumQueries(0):
            self.assertCountEqual(
                bookwithyear1.bookreview_set.all(), [self.bookreview1]
            )
        with self.assertNumQueries(0):
            prefetch_related_objects([bookwithyear1], "bookreview_set")
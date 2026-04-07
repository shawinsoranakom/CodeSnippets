def test_foreignkey_to_inherited(self):
        with self.assertNumQueries(2):
            qs = BookReview.objects.prefetch_related("book")
            titles = [obj.book.title for obj in qs]
        self.assertCountEqual(titles, ["Poems", "More poems"])
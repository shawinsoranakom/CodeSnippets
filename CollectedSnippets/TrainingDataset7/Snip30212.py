def test_prefetch_GFK_fk_pk(self):
        book = Book.objects.create(title="Poems")
        book_with_year = BookWithYear.objects.create(book=book, published_year=2019)
        Comment.objects.create(comment="awesome", content_object=book_with_year)
        qs = Comment.objects.prefetch_related("content_object")
        self.assertEqual([c.content_object for c in qs], [book_with_year])
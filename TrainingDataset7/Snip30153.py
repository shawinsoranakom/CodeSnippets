def test_onetoone_reverse_no_match(self):
        # Regression for #17439
        with self.assertNumQueries(2):
            book = Book.objects.prefetch_related("bookwithyear").all()[0]
        with self.assertNumQueries(0):
            with self.assertRaises(BookWithYear.DoesNotExist):
                book.bookwithyear
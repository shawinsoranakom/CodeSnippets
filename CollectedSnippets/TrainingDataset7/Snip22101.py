def test_reuse_same_filtered_relation(self):
        borrower = Borrower.objects.create(name="Jenny")
        Reservation.objects.create(
            borrower=borrower,
            book=self.book1,
            state=Reservation.STOPPED,
        )
        condition = Q(book__reservation__state=Reservation.STOPPED)
        my_reserved_books = FilteredRelation("book__reservation", condition=condition)
        first_query = list(
            Author.objects.annotate(
                my_reserved_books=my_reserved_books,
            )
        )
        self.assertEqual(my_reserved_books.condition, condition)
        second_query = list(
            Author.objects.annotate(
                my_reserved_books=my_reserved_books,
            )
        )
        self.assertEqual(first_query, second_query)
def test_three_level_nested_chained_relations(self):
        borrower = Borrower.objects.create(name="Jenny")
        Reservation.objects.create(
            borrower=borrower,
            book=self.book1,
            state=Reservation.STOPPED,
        )
        qs = Author.objects.annotate(
            my_books=FilteredRelation("book"),
            my_reserved_books=FilteredRelation(
                "my_books__reservation",
                condition=Q(my_books__reservation__state=Reservation.STOPPED),
            ),
            my_readers=FilteredRelation(
                "my_reserved_books__borrower",
                condition=Q(my_reserved_books__borrower=borrower),
            ),
        )
        self.assertSequenceEqual(
            qs.filter(my_readers=borrower).values_list("name", flat=True), ["Alice"]
        )
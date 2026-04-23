def test_mti_annotations(self):
        """
        Fields on an inherited model can be referenced by an
        annotated field.
        """
        d = DepartmentStore.objects.create(
            name="Angus & Robinson",
            original_opening=datetime.date(2014, 3, 8),
            friday_night_closing=datetime.time(21, 00, 00),
            chain="Westfield",
        )

        books = Book.objects.filter(rating__gt=4)
        for b in books:
            d.books.add(b)

        qs = (
            DepartmentStore.objects.annotate(
                other_name=F("name"),
                other_chain=F("chain"),
                is_open=Value(True, BooleanField()),
                book_isbn=F("books__isbn"),
            )
            .order_by("book_isbn")
            .filter(chain="Westfield")
        )

        self.assertQuerySetEqual(
            qs,
            [
                ("Angus & Robinson", "Westfield", True, "155860191"),
                ("Angus & Robinson", "Westfield", True, "159059725"),
            ],
            lambda d: (d.other_name, d.other_chain, d.is_open, d.book_isbn),
        )
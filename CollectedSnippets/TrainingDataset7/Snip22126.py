def setUpTestData(cls):
        cls.author1 = Author.objects.create(name="Alice")
        cls.editor_a = Editor.objects.create(name="a")
        cls.book1 = Book.objects.create(
            title="Poem by Alice",
            editor=cls.editor_a,
            author=cls.author1,
        )
        cls.borrower1 = Borrower.objects.create(name="Jenny")
        cls.borrower2 = Borrower.objects.create(name="Kevin")
        # borrower 1 reserves, rents, and returns book1.
        Reservation.objects.create(
            borrower=cls.borrower1,
            book=cls.book1,
            state=Reservation.STOPPED,
        )
        RentalSession.objects.create(
            borrower=cls.borrower1,
            book=cls.book1,
            state=RentalSession.STOPPED,
        )
        # borrower2 reserves, rents, and returns book1.
        Reservation.objects.create(
            borrower=cls.borrower2,
            book=cls.book1,
            state=Reservation.STOPPED,
        )
        RentalSession.objects.create(
            borrower=cls.borrower2,
            book=cls.book1,
            state=RentalSession.STOPPED,
        )
def setUpTestData(cls):
        cls.book1, cls.book2 = [
            Book.objects.create(title="book1"),
            Book.objects.create(title="book2"),
        ]
        cls.author11, cls.author12, cls.author21 = [
            Author.objects.create(first_book=cls.book1, name="Author11"),
            Author.objects.create(first_book=cls.book1, name="Author12"),
            Author.objects.create(first_book=cls.book2, name="Author21"),
        ]
        cls.author1_address1, cls.author1_address2, cls.author2_address1 = [
            AuthorAddress.objects.create(author=cls.author11, address="Happy place"),
            AuthorAddress.objects.create(author=cls.author12, address="Haunted house"),
            AuthorAddress.objects.create(author=cls.author21, address="Happy place"),
        ]
        cls.bookwithyear1 = BookWithYear.objects.create(
            title="Poems", published_year=2010
        )
        cls.bookreview1 = BookReview.objects.create(book=cls.bookwithyear1)
def setUpTestData(cls):
        cls.book = Book.objects.create(title="Poems")
        cls.author1 = Author.objects.create(name="Jane", first_book=cls.book)
        cls.author2 = Author.objects.create(name="Tom", first_book=cls.book)
        cls.author3 = Author.objects.create(name="Robert", first_book=cls.book)
        cls.author_address = AuthorAddress.objects.create(
            author=cls.author1, address="SomeStreet 1"
        )
        FavoriteAuthors.objects.create(author=cls.author1, likes_author=cls.author2)
        FavoriteAuthors.objects.create(author=cls.author2, likes_author=cls.author3)
        FavoriteAuthors.objects.create(author=cls.author3, likes_author=cls.author1)
def setUpTestData(cls):
        cls.book1 = Book.objects.create(title="Les confessions Volume I")
        cls.book2 = Book.objects.create(title="Candide")
        cls.author1 = AuthorWithAge.objects.create(
            name="Rousseau", first_book=cls.book1, age=70
        )
        cls.author2 = AuthorWithAge.objects.create(
            name="Voltaire", first_book=cls.book2, age=65
        )
        cls.book1.authors.add(cls.author1)
        cls.book2.authors.add(cls.author2)
        FavoriteAuthors.objects.create(author=cls.author1, likes_author=cls.author2)
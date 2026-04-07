def setUpTestData(cls):
        cls.book1 = BookWithYear.objects.create(title="Poems", published_year=2010)
        cls.book2 = BookWithYear.objects.create(title="More poems", published_year=2011)
        cls.author1 = AuthorWithAge.objects.create(
            name="Jane", first_book=cls.book1, age=50
        )
        cls.author2 = AuthorWithAge.objects.create(
            name="Tom", first_book=cls.book1, age=49
        )
        cls.author3 = AuthorWithAge.objects.create(
            name="Robert", first_book=cls.book2, age=48
        )
        cls.author_address = AuthorAddress.objects.create(
            author=cls.author1, address="SomeStreet 1"
        )
        cls.book2.aged_authors.add(cls.author2, cls.author3)
        cls.br1 = BookReview.objects.create(book=cls.book1, notes="review book1")
        cls.br2 = BookReview.objects.create(book=cls.book2, notes="review book2")
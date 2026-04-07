def setUpTestData(cls):
        cls.author1 = Author.objects.create(name="Alice")
        cls.author2 = Author.objects.create(name="Jane")
        cls.editor_a = Editor.objects.create(name="a")
        cls.editor_b = Editor.objects.create(name="b")
        cls.book1 = Book.objects.create(
            title="Poem by Alice",
            editor=cls.editor_a,
            author=cls.author1,
        )
        cls.book1.generic_author.set([cls.author2])
        cls.book2 = Book.objects.create(
            title="The book by Jane A",
            editor=cls.editor_b,
            author=cls.author2,
        )
        cls.book3 = Book.objects.create(
            title="The book by Jane B",
            editor=cls.editor_b,
            author=cls.author2,
        )
        cls.book4 = Book.objects.create(
            title="The book by Alice",
            editor=cls.editor_a,
            author=cls.author1,
        )
        cls.author1.favorite_books.add(cls.book2)
        cls.author1.favorite_books.add(cls.book3)
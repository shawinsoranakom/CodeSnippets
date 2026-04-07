def setUpTestData(cls):
        cls.book = Book.objects.create(title="Book1")
        cls.related1 = Author.objects.create(name="related1", first_book=cls.book)
        cls.related2 = Author.objects.create(name="related2", first_book=cls.book)
        cls.related3 = Author.objects.create(name="related3", first_book=cls.book)
        cls.related4 = Author.objects.create(name="related4", first_book=cls.book)

        cls.child = AuthorWithAgeChild.objects.create(
            name="child",
            age=31,
            first_book=cls.book,
        )
        cls.m2m_child = AuthorWithAgeChild.objects.create(
            name="m2m_child",
            age=31,
            first_book=cls.book,
        )
        cls.m2m_child.favorite_authors.set([cls.related1, cls.related2, cls.related3])
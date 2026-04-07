def setUpTestData(cls):
        book1 = Book.objects.create(title="Poems")
        book2 = Book.objects.create(title="Jane Eyre")
        book3 = Book.objects.create(title="Wuthering Heights")
        book4 = Book.objects.create(title="Sense and Sensibility")

        author1 = Author2.objects.create(name="Charlotte", first_book=book1)
        author2 = Author2.objects.create(name="Anne", first_book=book1)
        author3 = Author2.objects.create(name="Emily", first_book=book1)
        author4 = Author2.objects.create(name="Jane", first_book=book4)

        author1.favorite_books.add(book1, book2, book3)
        author2.favorite_books.add(book1)
        author3.favorite_books.add(book2)
        author4.favorite_books.add(book3)
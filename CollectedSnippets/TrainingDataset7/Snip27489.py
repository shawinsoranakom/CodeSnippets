def inner_method(models, schema_editor):
            Author = models.get_model("test_authors", "Author")
            Book = models.get_model("test_books", "Book")
            author = Author.objects.create(name="Hemingway")
            Book.objects.create(title="Old Man and The Sea", author=author)
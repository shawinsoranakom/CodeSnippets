def test_other_creation(self):
        """
        Objects created on another database don't leak onto the default
        database
        """
        # Create a book on the second database
        Book.objects.using("other").create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        # Create a book on the default database using a save
        dive = Book()
        dive.title = "Dive into Python"
        dive.published = datetime.date(2009, 5, 4)
        dive.save(using="other")

        # Book exists on the default database, but not on other database
        try:
            Book.objects.using("other").get(title="Pro Django")
        except Book.DoesNotExist:
            self.fail('"Pro Django" should exist on other database')

        with self.assertRaises(Book.DoesNotExist):
            Book.objects.get(title="Pro Django")
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.using("default").get(title="Pro Django")

        try:
            Book.objects.using("other").get(title="Dive into Python")
        except Book.DoesNotExist:
            self.fail('"Dive into Python" should exist on other database')

        with self.assertRaises(Book.DoesNotExist):
            Book.objects.get(title="Dive into Python")
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.using("default").get(title="Dive into Python")
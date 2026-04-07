def test_fixture_loading(self):
        "Multi-db fixtures are loaded correctly"
        # "Pro Django" exists on the default database, but not on other
        # database
        Book.objects.get(title="Pro Django")
        Book.objects.using("default").get(title="Pro Django")

        with self.assertRaises(Book.DoesNotExist):
            Book.objects.using("other").get(title="Pro Django")

        # "Dive into Python" exists on the default database, but not on other
        # database
        Book.objects.using("other").get(title="Dive into Python")

        with self.assertRaises(Book.DoesNotExist):
            Book.objects.get(title="Dive into Python")
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.using("default").get(title="Dive into Python")

        # "Definitive Guide" exists on the both databases
        Book.objects.get(title="The Definitive Guide to Django")
        Book.objects.using("default").get(title="The Definitive Guide to Django")
        Book.objects.using("other").get(title="The Definitive Guide to Django")
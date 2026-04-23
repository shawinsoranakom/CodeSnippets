def test_basic_queries(self):
        "Queries are constrained to a single database"
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        dive = Book.objects.using("other").get(published=datetime.date(2009, 5, 4))
        self.assertEqual(dive.title, "Dive into Python")
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.using("default").get(published=datetime.date(2009, 5, 4))

        dive = Book.objects.using("other").get(title__icontains="dive")
        self.assertEqual(dive.title, "Dive into Python")
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.using("default").get(title__icontains="dive")

        dive = Book.objects.using("other").get(title__iexact="dive INTO python")
        self.assertEqual(dive.title, "Dive into Python")
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.using("default").get(title__iexact="dive INTO python")

        dive = Book.objects.using("other").get(published__year=2009)
        self.assertEqual(dive.title, "Dive into Python")
        self.assertEqual(dive.published, datetime.date(2009, 5, 4))
        with self.assertRaises(Book.DoesNotExist):
            Book.objects.using("default").get(published__year=2009)

        years = Book.objects.using("other").dates("published", "year")
        self.assertEqual([o.year for o in years], [2009])
        years = Book.objects.using("default").dates("published", "year")
        self.assertEqual([o.year for o in years], [])

        months = Book.objects.using("other").dates("published", "month")
        self.assertEqual([o.month for o in months], [5])
        months = Book.objects.using("default").dates("published", "month")
        self.assertEqual([o.month for o in months], [])
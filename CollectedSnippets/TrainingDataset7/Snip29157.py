def test_ordering(self):
        "get_next_by_XXX commands stick to a single database"
        Book.objects.create(title="Pro Django", published=datetime.date(2008, 12, 16))
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        learn = Book.objects.using("other").create(
            title="Learning Python", published=datetime.date(2008, 7, 16)
        )

        self.assertEqual(learn.get_next_by_published().title, "Dive into Python")
        self.assertEqual(dive.get_previous_by_published().title, "Learning Python")
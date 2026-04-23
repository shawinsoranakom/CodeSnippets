def test_invalid_set_foreign_key_assignment(self):
        marty = Person.objects.using("default").create(name="Marty Alchin")
        dive = Book.objects.using("other").create(
            title="Dive into Python",
            published=datetime.date(2009, 5, 4),
        )
        # Set a foreign key set with an object from a different database
        msg = (
            "<Book: Dive into Python> instance isn't saved. Use bulk=False or save the "
            "object first."
        )
        with self.assertRaisesMessage(ValueError, msg):
            marty.edited.set([dive])
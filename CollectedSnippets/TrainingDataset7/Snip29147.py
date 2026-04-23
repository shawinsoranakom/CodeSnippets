def test_foreign_key_cross_database_protection(self):
        """
        Operations that involve sharing FK objects across databases raise an
        error
        """
        # Create a book and author on the default database
        pro = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        marty = Person.objects.create(name="Marty Alchin")

        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        # Set a foreign key with an object from a different database
        msg = (
            'Cannot assign "<Person: Marty Alchin>": the current database '
            "router prevents this relation."
        )
        with self.assertRaisesMessage(ValueError, msg):
            dive.editor = marty

        # Set a foreign key set with an object from a different database
        with self.assertRaisesMessage(ValueError, msg):
            with transaction.atomic(using="default"):
                marty.edited.set([pro, dive])

        # Add to a foreign key set with an object from a different database
        with self.assertRaisesMessage(ValueError, msg):
            with transaction.atomic(using="default"):
                marty.edited.add(dive)
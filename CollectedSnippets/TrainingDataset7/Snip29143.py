def test_m2m_cross_database_protection(self):
        """
        Operations that involve sharing M2M objects across databases raise an
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

        mark = Person.objects.using("other").create(name="Mark Pilgrim")
        # Set a foreign key set with an object from a different database
        msg = (
            'Cannot assign "<Person: Marty Alchin>": the current database '
            "router prevents this relation."
        )
        with self.assertRaisesMessage(ValueError, msg):
            with transaction.atomic(using="default"):
                marty.edited.set([pro, dive])

        # Add to an m2m with an object from a different database
        msg = (
            'Cannot add "<Book: Dive into Python>": instance is on '
            'database "default", value is on database "other"'
        )
        with self.assertRaisesMessage(ValueError, msg):
            with transaction.atomic(using="default"):
                marty.book_set.add(dive)

        # Set a m2m with an object from a different database
        with self.assertRaisesMessage(ValueError, msg):
            with transaction.atomic(using="default"):
                marty.book_set.set([pro, dive])

        # Add to a reverse m2m with an object from a different database
        msg = (
            'Cannot add "<Person: Marty Alchin>": instance is on '
            'database "other", value is on database "default"'
        )
        with self.assertRaisesMessage(ValueError, msg):
            with transaction.atomic(using="other"):
                dive.authors.add(marty)

        # Set a reverse m2m with an object from a different database
        with self.assertRaisesMessage(ValueError, msg):
            with transaction.atomic(using="other"):
                dive.authors.set([mark, marty])
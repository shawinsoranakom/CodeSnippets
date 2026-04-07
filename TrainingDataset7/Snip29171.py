def test_m2m_cross_database_protection(self):
        "M2M relations can cross databases if the database share a source"
        # Create books and authors on the inverse to the usual database
        pro = Book.objects.using("other").create(
            pk=1, title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        marty = Person.objects.using("other").create(pk=1, name="Marty Alchin")

        dive = Book.objects.using("default").create(
            pk=2, title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        mark = Person.objects.using("default").create(pk=2, name="Mark Pilgrim")

        # Now save back onto the usual database.
        # This simulates primary/replica - the objects exist on both database,
        # but the _state.db is as it is for all other tests.
        pro.save(using="default")
        marty.save(using="default")
        dive.save(using="other")
        mark.save(using="other")

        # We have 2 of both types of object on both databases
        self.assertEqual(Book.objects.using("default").count(), 2)
        self.assertEqual(Book.objects.using("other").count(), 2)
        self.assertEqual(Person.objects.using("default").count(), 2)
        self.assertEqual(Person.objects.using("other").count(), 2)

        # Set a m2m set with an object from a different database
        marty.book_set.set([pro, dive])

        # Database assignments don't change
        self.assertEqual(marty._state.db, "default")
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(dive._state.db, "other")
        self.assertEqual(mark._state.db, "other")

        # All m2m relations should be saved on the default database
        self.assertEqual(Book.authors.through.objects.using("default").count(), 2)
        self.assertEqual(Book.authors.through.objects.using("other").count(), 0)

        # Reset relations
        Book.authors.through.objects.using("default").delete()

        # Add to an m2m with an object from a different database
        marty.book_set.add(dive)

        # Database assignments don't change
        self.assertEqual(marty._state.db, "default")
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(dive._state.db, "other")
        self.assertEqual(mark._state.db, "other")

        # All m2m relations should be saved on the default database
        self.assertEqual(Book.authors.through.objects.using("default").count(), 1)
        self.assertEqual(Book.authors.through.objects.using("other").count(), 0)

        # Reset relations
        Book.authors.through.objects.using("default").delete()

        # Set a reverse m2m with an object from a different database
        dive.authors.set([mark, marty])

        # Database assignments don't change
        self.assertEqual(marty._state.db, "default")
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(dive._state.db, "other")
        self.assertEqual(mark._state.db, "other")

        # All m2m relations should be saved on the default database
        self.assertEqual(Book.authors.through.objects.using("default").count(), 2)
        self.assertEqual(Book.authors.through.objects.using("other").count(), 0)

        # Reset relations
        Book.authors.through.objects.using("default").delete()

        self.assertEqual(Book.authors.through.objects.using("default").count(), 0)
        self.assertEqual(Book.authors.through.objects.using("other").count(), 0)

        # Add to a reverse m2m with an object from a different database
        dive.authors.add(marty)

        # Database assignments don't change
        self.assertEqual(marty._state.db, "default")
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(dive._state.db, "other")
        self.assertEqual(mark._state.db, "other")

        # All m2m relations should be saved on the default database
        self.assertEqual(Book.authors.through.objects.using("default").count(), 1)
        self.assertEqual(Book.authors.through.objects.using("other").count(), 0)

        # If you create an object through a M2M relation, it will be
        # written to the write database, even if the original object
        # was on the read database
        alice = dive.authors.create(name="Alice", pk=3)
        self.assertEqual(alice._state.db, "default")

        # Same goes for get_or_create, regardless of whether getting or
        # creating
        alice, created = dive.authors.get_or_create(name="Alice")
        self.assertEqual(alice._state.db, "default")

        bob, created = dive.authors.get_or_create(name="Bob", defaults={"pk": 4})
        self.assertEqual(bob._state.db, "default")
def test_foreign_key_cross_database_protection(self):
        """
        Foreign keys can cross databases if they two databases have a common
        source
        """
        # Create a book and author on the default database
        pro = Book.objects.using("default").create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        marty = Person.objects.using("default").create(name="Marty Alchin")

        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        mark = Person.objects.using("other").create(name="Mark Pilgrim")

        # Set a foreign key with an object from a different database
        dive.editor = marty

        # Database assignments of original objects haven't changed...
        self.assertEqual(marty._state.db, "default")
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(dive._state.db, "other")
        self.assertEqual(mark._state.db, "other")

        # ... but they will when the affected object is saved.
        dive.save()
        self.assertEqual(dive._state.db, "default")

        # ...and the source database now has a copy of any object saved
        Book.objects.using("default").get(title="Dive into Python").delete()

        # This isn't a real primary/replica database, so restore the original
        # from other
        dive = Book.objects.using("other").get(title="Dive into Python")
        self.assertEqual(dive._state.db, "other")

        # Set a foreign key set with an object from a different database
        marty.edited.set([pro, dive], bulk=False)

        # Assignment implies a save, so database assignments of original
        # objects have changed...
        self.assertEqual(marty._state.db, "default")
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(dive._state.db, "default")
        self.assertEqual(mark._state.db, "other")

        # ...and the source database now has a copy of any object saved
        Book.objects.using("default").get(title="Dive into Python").delete()

        # This isn't a real primary/replica database, so restore the original
        # from other
        dive = Book.objects.using("other").get(title="Dive into Python")
        self.assertEqual(dive._state.db, "other")

        # Add to a foreign key set with an object from a different database
        marty.edited.add(dive, bulk=False)

        # Add implies a save, so database assignments of original objects have
        # changed...
        self.assertEqual(marty._state.db, "default")
        self.assertEqual(pro._state.db, "default")
        self.assertEqual(dive._state.db, "default")
        self.assertEqual(mark._state.db, "other")

        # ...and the source database now has a copy of any object saved
        Book.objects.using("default").get(title="Dive into Python").delete()

        # This isn't a real primary/replica database, so restore the original
        # from other
        dive = Book.objects.using("other").get(title="Dive into Python")

        # If you assign a FK object when the base object hasn't
        # been saved yet, you implicitly assign the database for the
        # base object.
        chris = Person(name="Chris Mills")
        html5 = Book(title="Dive into HTML5", published=datetime.date(2010, 3, 15))
        # initially, no db assigned
        self.assertIsNone(chris._state.db)
        self.assertIsNone(html5._state.db)

        # old object comes from 'other', so the new object is set to use the
        # source of 'other'...
        self.assertEqual(dive._state.db, "other")
        chris.save()
        dive.editor = chris
        html5.editor = mark

        self.assertEqual(dive._state.db, "other")
        self.assertEqual(mark._state.db, "other")
        self.assertEqual(chris._state.db, "default")
        self.assertEqual(html5._state.db, "default")

        # This also works if you assign the FK in the constructor
        water = Book(
            title="Dive into Water", published=datetime.date(2001, 1, 1), editor=mark
        )
        self.assertEqual(water._state.db, "default")

        # For the remainder of this test, create a copy of 'mark' in the
        # 'default' database to prevent integrity errors on backends that
        # don't defer constraints checks until the end of the transaction
        mark.save(using="default")

        # This moved 'mark' in the 'default' database, move it back in 'other'
        mark.save(using="other")
        self.assertEqual(mark._state.db, "other")

        # If you create an object through a FK relation, it will be
        # written to the write database, even if the original object
        # was on the read database
        cheesecake = mark.edited.create(
            title="Dive into Cheesecake", published=datetime.date(2010, 3, 15)
        )
        self.assertEqual(cheesecake._state.db, "default")

        # Same goes for get_or_create, regardless of whether getting or
        # creating
        cheesecake, created = mark.edited.get_or_create(
            title="Dive into Cheesecake",
            published=datetime.date(2010, 3, 15),
        )
        self.assertEqual(cheesecake._state.db, "default")

        puddles, created = mark.edited.get_or_create(
            title="Dive into Puddles", published=datetime.date(2010, 3, 15)
        )
        self.assertEqual(puddles._state.db, "default")
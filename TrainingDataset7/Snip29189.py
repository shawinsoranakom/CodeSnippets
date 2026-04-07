def test_database_arg_m2m(self):
        """
        The m2m_changed signal has a correct database arg.
        """
        # Make a receiver
        receiver = DatabaseReceiver()
        # Connect it
        signals.m2m_changed.connect(receiver=receiver)

        # Create the models that will be used for the tests
        b = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        p = Person.objects.create(name="Marty Alchin")

        # Create a copy of the models on the 'other' database to prevent
        # integrity errors on backends that don't defer constraints checks
        Book.objects.using("other").create(
            pk=b.pk, title=b.title, published=b.published
        )
        Person.objects.using("other").create(pk=p.pk, name=p.name)

        # Test addition
        b.authors.add(p)
        self.assertEqual(receiver._database, DEFAULT_DB_ALIAS)
        with self.override_router():
            b.authors.add(p)
        self.assertEqual(receiver._database, "other")

        # Test removal
        b.authors.remove(p)
        self.assertEqual(receiver._database, DEFAULT_DB_ALIAS)
        with self.override_router():
            b.authors.remove(p)
        self.assertEqual(receiver._database, "other")

        # Test addition in reverse
        p.book_set.add(b)
        self.assertEqual(receiver._database, DEFAULT_DB_ALIAS)
        with self.override_router():
            p.book_set.add(b)
        self.assertEqual(receiver._database, "other")

        # Test clearing
        b.authors.clear()
        self.assertEqual(receiver._database, DEFAULT_DB_ALIAS)
        with self.override_router():
            b.authors.clear()
        self.assertEqual(receiver._database, "other")
def test_database_routing(self):
        marty = Person.objects.using("default").create(name="Marty Alchin")
        pro = Book.objects.using("default").create(
            title="Pro Django",
            published=datetime.date(2008, 12, 16),
            editor=marty,
        )
        pro.authors.set([marty])

        # Create a book and author on the other database
        Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        # An update query will be routed to the default database
        Book.objects.filter(title="Pro Django").update(pages=200)

        with self.assertRaises(Book.DoesNotExist):
            # By default, the get query will be directed to 'other'
            Book.objects.get(title="Pro Django")

        # But the same query issued explicitly at a database will work.
        pro = Book.objects.using("default").get(title="Pro Django")

        # The update worked.
        self.assertEqual(pro.pages, 200)

        # An update query with an explicit using clause will be routed
        # to the requested database.
        Book.objects.using("other").filter(title="Dive into Python").update(pages=300)
        self.assertEqual(Book.objects.get(title="Dive into Python").pages, 300)

        # Related object queries stick to the same database
        # as the original object, regardless of the router
        self.assertEqual(
            list(pro.authors.values_list("name", flat=True)), ["Marty Alchin"]
        )
        self.assertEqual(pro.editor.name, "Marty Alchin")

        # get_or_create is a special case. The get needs to be targeted at
        # the write database in order to avoid potential transaction
        # consistency problems
        book, created = Book.objects.get_or_create(title="Pro Django")
        self.assertFalse(created)

        book, created = Book.objects.get_or_create(
            title="Dive Into Python", defaults={"published": datetime.date(2009, 5, 4)}
        )
        self.assertTrue(created)

        # Check the head count of objects
        self.assertEqual(Book.objects.using("default").count(), 2)
        self.assertEqual(Book.objects.using("other").count(), 1)
        # If a database isn't specified, the read database is used
        self.assertEqual(Book.objects.count(), 1)

        # A delete query will also be routed to the default database
        Book.objects.filter(pages__gt=150).delete()

        # The default database has lost the book.
        self.assertEqual(Book.objects.using("default").count(), 1)
        self.assertEqual(Book.objects.using("other").count(), 1)
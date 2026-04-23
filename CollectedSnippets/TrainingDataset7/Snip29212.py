def test_m2m_get_or_create(self):
        Person.objects.create(name="Someone")
        book = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        with self.assertRaises(RouterUsed) as cm:
            with self.override_router():
                book.authors.get_or_create(name="Someone else")
        e = cm.exception
        self.assertEqual(e.mode, RouterUsed.WRITE)
        self.assertEqual(e.model, Book)
        self.assertEqual(e.hints, {"instance": book})
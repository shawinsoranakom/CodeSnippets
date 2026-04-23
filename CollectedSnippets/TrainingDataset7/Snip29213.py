def test_m2m_remove(self):
        auth = Person.objects.create(name="Someone")
        book = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        book.authors.add(auth)
        with self.assertRaises(RouterUsed) as cm:
            with self.override_router():
                book.authors.remove(auth)
        e = cm.exception
        self.assertEqual(e.mode, RouterUsed.WRITE)
        self.assertEqual(e.model, Book.authors.through)
        self.assertEqual(e.hints, {"instance": book})
def test_reverse_m2m_update(self):
        auth = Person.objects.create(name="Someone")
        book = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )
        book.authors.add(auth)
        with self.assertRaises(RouterUsed) as cm:
            with self.override_router():
                auth.book_set.update(title="Different")
        e = cm.exception
        self.assertEqual(e.mode, RouterUsed.WRITE)
        self.assertEqual(e.model, Book)
        self.assertEqual(e.hints, {"instance": auth})
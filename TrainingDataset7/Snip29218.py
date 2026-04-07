def test_reverse_m2m_get_or_create(self):
        auth = Person.objects.create(name="Someone")
        Book.objects.create(title="Pro Django", published=datetime.date(2008, 12, 16))
        with self.assertRaises(RouterUsed) as cm:
            with self.override_router():
                auth.book_set.get_or_create(
                    title="New Book", published=datetime.datetime.now()
                )
        e = cm.exception
        self.assertEqual(e.mode, RouterUsed.WRITE)
        self.assertEqual(e.model, Person)
        self.assertEqual(e.hints, {"instance": auth})
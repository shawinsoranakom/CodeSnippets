def test_pickling(self):
        for db in self.databases:
            Book.objects.using(db).create(
                title="Dive into Python", published=datetime.date(2009, 5, 4)
            )
            qs = Book.objects.all()
            self.assertEqual(qs.db, pickle.loads(pickle.dumps(qs)).db)
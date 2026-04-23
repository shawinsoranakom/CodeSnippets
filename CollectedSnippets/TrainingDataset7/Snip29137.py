def test_refresh(self):
        dive = Book(title="Dive into Python", published=datetime.date(2009, 5, 4))
        dive.save(using="other")
        dive2 = Book.objects.using("other").get()
        dive2.title = "Dive into Python (on default)"
        dive2.save(using="default")
        dive.refresh_from_db()
        self.assertEqual(dive.title, "Dive into Python")
        dive.refresh_from_db(using="default")
        self.assertEqual(dive.title, "Dive into Python (on default)")
        self.assertEqual(dive._state.db, "default")
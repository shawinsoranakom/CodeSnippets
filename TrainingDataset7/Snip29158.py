def test_raw(self):
        "test the raw() method across databases"
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        val = Book.objects.db_manager("other").raw(
            "SELECT id FROM multiple_database_book"
        )
        self.assertQuerySetEqual(val, [dive.pk], attrgetter("pk"))

        val = Book.objects.raw("SELECT id FROM multiple_database_book").using("other")
        self.assertQuerySetEqual(val, [dive.pk], attrgetter("pk"))
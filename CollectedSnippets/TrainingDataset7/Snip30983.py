def test_missing_fields_fetch_mode_raise(self):
        query = "SELECT id, first_name, dob FROM raw_query_author"
        authors = list(Author.objects.fetch_mode(RAISE).raw(query))
        msg = "Fetching of Author.last_name blocked."
        with self.assertRaisesMessage(FieldFetchBlocked, msg) as cm:
            authors[0].last_name
        self.assertIsNone(cm.exception.__cause__)
        self.assertTrue(cm.exception.__suppress_context__)
        self.assertTrue(cm.exception.__suppress_context__)
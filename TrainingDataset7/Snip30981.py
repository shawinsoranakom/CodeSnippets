def test_missing_fields_without_PK(self):
        query = "SELECT first_name, dob FROM raw_query_author"
        msg = "Raw query must include the primary key"
        with self.assertRaisesMessage(FieldDoesNotExist, msg):
            list(Author.objects.raw(query))
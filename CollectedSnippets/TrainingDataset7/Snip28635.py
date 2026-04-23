def test_index_fields_strings(self):
        msg = "Index.fields must contain only strings with field names."
        with self.assertRaisesMessage(ValueError, msg):
            models.Index(fields=[models.F("title")])
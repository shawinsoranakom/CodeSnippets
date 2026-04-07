def test_fields_tuple(self):
        self.assertEqual(models.Index(fields=("title",)).fields, ["title"])
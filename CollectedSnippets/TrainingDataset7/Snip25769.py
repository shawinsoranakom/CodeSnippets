def test_in_bulk_non_unique_field(self):
        msg = "in_bulk()'s field_name must be a unique field but 'author' isn't."
        with self.assertRaisesMessage(ValueError, msg):
            Article.objects.in_bulk([self.au1], field_name="author")
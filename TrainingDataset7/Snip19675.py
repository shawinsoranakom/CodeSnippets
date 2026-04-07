def test_bulk_update_primary_key_fields(self):
        message = "bulk_update() cannot be used with primary key fields."
        with self.assertRaisesMessage(ValueError, message):
            Comment.objects.bulk_update([self.comment_1, self.comment_2], ["id"])
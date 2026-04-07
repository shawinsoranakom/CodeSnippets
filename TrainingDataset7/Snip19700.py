def test_in_bulk_values(self):
        result = Comment.objects.values().in_bulk([self.comment.pk])
        self.assertEqual(
            result,
            {
                self.comment.pk: {
                    "tenant_id": self.comment.tenant_id,
                    "id": self.comment.id,
                    "user_id": self.comment.user_id,
                    "text": self.comment.text,
                    "integer": self.comment.integer,
                }
            },
        )
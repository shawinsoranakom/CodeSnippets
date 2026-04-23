def test_error_on_comment_pk_conflict(self):
        with self.assertRaises(IntegrityError):
            Comment.objects.create(tenant=self.tenant, id=self.comment.id, user_id=1)
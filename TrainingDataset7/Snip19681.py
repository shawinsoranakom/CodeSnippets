def test_cant_update_pk_field(self):
        qs = Comment.objects.filter(user__email=self.user_1.email)
        msg = "Composite primary key fields must be updated individually."
        with self.assertRaisesMessage(FieldError, msg):
            qs.update(pk=(1, 10))
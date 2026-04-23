def test_cant_update_relation(self):
        msg = (
            "Cannot update model field <django.db.models.fields.related.ForeignObject: "
            "user> (only concrete fields are permitted)"
        )

        with self.assertRaisesMessage(FieldError, msg):
            Comment.objects.update(user=self.user_1)

        with self.assertRaisesMessage(FieldError, msg):
            Comment.objects.update(user=User())
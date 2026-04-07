def test_update_value_not_composite(self):
        msg = (
            "Composite primary keys expressions are not allowed in this "
            "query (text=F('pk'))."
        )
        with self.assertRaisesMessage(FieldError, msg):
            Comment.objects.update(text=F("pk"))
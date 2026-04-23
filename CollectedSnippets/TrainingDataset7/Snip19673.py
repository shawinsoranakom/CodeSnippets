def test_update_fields_pk_field(self):
        msg = (
            "The following fields do not exist in this model, are m2m fields, "
            "primary keys, or are non-concrete fields: id"
        )
        with self.assertRaisesMessage(ValueError, msg):
            self.user_1.save(update_fields=["id"])
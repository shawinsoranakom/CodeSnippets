def test_nonexistent_field(self):
        with self.assertRaisesMessage(
            FieldDoesNotExist, "Note has no field named 'nonexistent'"
        ):
            Note.objects.bulk_update([], ["nonexistent"])
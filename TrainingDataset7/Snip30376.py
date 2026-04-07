def test_no_fields(self):
        msg = "Field names must be given to bulk_update()."
        with self.assertRaisesMessage(ValueError, msg):
            Note.objects.bulk_update([], fields=[])
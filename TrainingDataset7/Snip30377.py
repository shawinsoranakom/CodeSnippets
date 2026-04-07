def test_invalid_batch_size(self):
        msg = "Batch size must be a positive integer."
        with self.assertRaisesMessage(ValueError, msg):
            Note.objects.bulk_update([], fields=["note"], batch_size=-1)
        with self.assertRaisesMessage(ValueError, msg):
            Note.objects.bulk_update([], fields=["note"], batch_size=0)
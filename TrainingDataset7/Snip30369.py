def test_batch_size(self):
        with self.assertNumQueries(len(self.notes)):
            Note.objects.bulk_update(self.notes, fields=["note"], batch_size=1)
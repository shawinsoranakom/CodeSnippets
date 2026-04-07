def test_updated_rows_when_passing_duplicates(self):
        note = Note.objects.create(note="test-note", misc="test")
        rows_updated = Note.objects.bulk_update([note, note], ["note"])
        self.assertEqual(rows_updated, 1)
        # Duplicates in different batches.
        rows_updated = Note.objects.bulk_update([note, note], ["note"], batch_size=1)
        self.assertEqual(rows_updated, 2)
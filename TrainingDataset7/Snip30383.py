def test_large_batch(self):
        Note.objects.bulk_create(
            [Note(note=str(i), misc=str(i)) for i in range(0, 2000)]
        )
        notes = list(Note.objects.all())
        rows_updated = Note.objects.bulk_update(notes, ["note"])
        self.assertEqual(rows_updated, 2000)
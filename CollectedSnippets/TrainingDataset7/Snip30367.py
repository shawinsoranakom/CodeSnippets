def test_simple(self):
        for note in self.notes:
            note.note = "test-%s" % note.id
        with self.assertNumQueries(1):
            Note.objects.bulk_update(self.notes, ["note"])
        self.assertCountEqual(
            Note.objects.values_list("note", flat=True),
            [cat.note for cat in self.notes],
        )
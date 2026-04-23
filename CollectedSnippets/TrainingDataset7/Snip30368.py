def test_multiple_fields(self):
        for note in self.notes:
            note.note = "test-%s" % note.id
            note.misc = "misc-%s" % note.id
        with self.assertNumQueries(1):
            Note.objects.bulk_update(self.notes, ["note", "misc"])
        self.assertCountEqual(
            Note.objects.values_list("note", flat=True),
            [cat.note for cat in self.notes],
        )
        self.assertCountEqual(
            Note.objects.values_list("misc", flat=True),
            [cat.misc for cat in self.notes],
        )
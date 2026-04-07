def test_functions(self):
        Note.objects.update(note="TEST")
        for note in self.notes:
            note.note = Lower("note")
        Note.objects.bulk_update(self.notes, ["note"])
        self.assertEqual(set(Note.objects.values_list("note", flat=True)), {"test"})
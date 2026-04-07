def test_f_expression(self):
        notes = [
            Note.objects.create(note="test_note", misc="test_misc") for _ in range(10)
        ]
        for note in notes:
            note.misc = F("note")
        Note.objects.bulk_update(notes, ["misc"])
        self.assertCountEqual(Note.objects.filter(misc="test_note"), notes)
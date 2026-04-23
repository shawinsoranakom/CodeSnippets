def test_boolean_conversion(self):
        # Aggregates mixed up ordering of columns for backend's convert_values
        # method. Refs #21126.
        e = Entries.objects.create(Entry="foo")
        c = Clues.objects.create(EntryID=e, Clue="bar")
        qs = Clues.objects.select_related("EntryID").annotate(Count("ID"))
        self.assertSequenceEqual(qs, [c])
        self.assertEqual(qs[0].EntryID, e)
        self.assertIs(qs[0].EntryID.Exclude, False)
def test_db_col_table(self):
        # Tests on fields with non-default table and column names.
        qs = Clues.objects.values("EntryID__Entry").annotate(
            Appearances=Count("EntryID"), Distinct_Clues=Count("Clue", distinct=True)
        )
        self.assertSequenceEqual(qs, [])

        qs = Entries.objects.annotate(clue_count=Count("clues__ID"))
        self.assertSequenceEqual(qs, [])
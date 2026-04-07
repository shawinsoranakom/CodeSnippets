def test_unique_together_meta(self):
        out = StringIO()
        call_command("inspectdb", "inspectdb_uniquetogether", stdout=out)
        output = out.getvalue()
        self.assertIn("    unique_together = (('", output)
        unique_together_match = self.unique_re.findall(output)
        # There should be one unique_together tuple.
        self.assertEqual(len(unique_together_match), 1)
        fields = unique_together_match[0]
        # Fields with db_column = field name.
        self.assertIn("('field1', 'field2')", fields)
        # Fields from columns whose names are Python keywords.
        self.assertIn("('field1', 'field2')", fields)
        # Fields whose names normalize to the same Python field name and hence
        # are given an integer suffix.
        self.assertIn("('non_unique_column', 'non_unique_column_0')", fields)
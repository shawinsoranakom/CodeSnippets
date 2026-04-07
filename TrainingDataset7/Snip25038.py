def test_po_remains_unchanged(self):
        """PO files are unchanged unless there are new changes."""
        _, po_contents = self._run_makemessages()
        self.assertEqual(po_contents, self.original_po_contents)
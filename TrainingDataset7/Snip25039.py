def test_po_changed_with_new_strings(self):
        """PO files are updated when new changes are detected."""
        Path("models.py.tmp").rename("models.py")
        _, po_contents = self._run_makemessages()
        self.assertNotEqual(po_contents, self.original_po_contents)
        self.assertMsgId(
            "This is a hitherto undiscovered translatable string.",
            po_contents,
        )
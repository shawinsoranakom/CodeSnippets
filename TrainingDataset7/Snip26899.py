def test_unmanaged_custom_pk(self):
        """
        #23415 - The autodetector must correctly deal with custom FK on
        unmanaged models.
        """
        # First, we test the default pk field name
        changes = self.get_changes([], [self.author_unmanaged_default_pk, self.book])
        # The model the FK on the book model points to.
        fk_field = changes["otherapp"][0].operations[0].fields[2][1]
        self.assertEqual(fk_field.remote_field.model, "testapp.Author")
        # Now, we test the custom pk field name
        changes = self.get_changes([], [self.author_unmanaged_custom_pk, self.book])
        # The model the FK on the book model points to.
        fk_field = changes["otherapp"][0].operations[0].fields[2][1]
        self.assertEqual(fk_field.remote_field.model, "testapp.Author")
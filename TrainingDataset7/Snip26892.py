def test_proxy_custom_pk(self):
        """
        #23415 - The autodetector must correctly deal with custom FK on proxy
        models.
        """
        # First, we test the default pk field name
        changes = self.get_changes(
            [], [self.author_empty, self.author_proxy_third, self.book_proxy_fk]
        )
        # The model the FK is pointing from and to.
        self.assertEqual(
            changes["otherapp"][0].operations[0].fields[2][1].remote_field.model,
            "thirdapp.AuthorProxy",
        )
        # Now, we test the custom pk field name
        changes = self.get_changes(
            [], [self.author_custom_pk, self.author_proxy_third, self.book_proxy_fk]
        )
        # The model the FK is pointing from and to.
        self.assertEqual(
            changes["otherapp"][0].operations[0].fields[2][1].remote_field.model,
            "thirdapp.AuthorProxy",
        )
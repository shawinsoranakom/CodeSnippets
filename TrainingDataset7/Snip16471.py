def test_deleteconfirmation_link(self):
        """
        The link from the delete confirmation page referring back to the
        changeform of the object should be quoted.
        """
        url = reverse(
            "admin:admin_views_modelwithstringprimarykey_delete", args=(quote(self.pk),)
        )
        response = self.client.get(url)
        # this URL now comes through reverse(), thus url quoting and iri_to_uri
        # encoding
        change_url = reverse(
            "admin:admin_views_modelwithstringprimarykey_change", args=("__fk__",)
        ).replace("__fk__", escape(iri_to_uri(quote(self.pk))))
        should_contain = '<a href="%s">%s</a>' % (change_url, escape(self.pk))
        self.assertContains(response, should_contain)
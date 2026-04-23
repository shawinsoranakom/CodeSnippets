def test_changelist_to_changeform_link(self):
        """
        Link to the changeform of the object in changelist should use reverse()
        and be quoted.
        """
        response = self.client.get(
            reverse("admin:admin_views_modelwithstringprimarykey_changelist")
        )
        # this URL now comes through reverse(), thus url quoting and iri_to_uri
        # encoding
        pk_final_url = escape(iri_to_uri(quote(self.pk)))
        change_url = reverse(
            "admin:admin_views_modelwithstringprimarykey_change", args=("__fk__",)
        ).replace("__fk__", pk_final_url)
        should_contain = '<th class="field-__str__"><a href="%s">%s</a></th>' % (
            change_url,
            escape(self.pk),
        )
        self.assertContains(response, should_contain)
def test_with_fk_to_field(self):
        """
        The to_field GET parameter is preserved when a search is performed.
        Refs #10918.
        """
        response = self.client.get(
            reverse("admin:auth_user_changelist") + "?q=joe&%s=id" % TO_FIELD_VAR
        )
        self.assertContains(response, "\n1 user\n")
        self.assertContains(
            response,
            '<input type="hidden" name="%s" value="id">' % TO_FIELD_VAR,
            html=True,
        )
def test_actions_ordering(self):
        """Actions are ordered as expected."""
        response = self.client.get(
            reverse("admin:admin_views_externalsubscriber_changelist")
        )
        self.assertContains(
            response,
            """<label>Action: <select name="action" required>
<option value="" selected>---------</option>
<option value="delete_selected">Delete selected external
subscribers</option>
<option value="redirect_to">Redirect to (Awesome action)</option>
<option value="external_mail">External mail (Another awesome
action)</option>
<option value="download">Download subscription</option>
<option value="no_perm">No permission to run</option>
</select>""",
            html=True,
        )
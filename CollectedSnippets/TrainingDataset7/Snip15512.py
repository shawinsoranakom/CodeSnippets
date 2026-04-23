def test_stacked_inline_single_hidden_field_in_line_with_view_only_permissions(
        self,
    ):
        """
        Content of hidden field is not visible in stacked inline when user has
        view-only permission and the field is grouped on a separate line.
        """
        self.client.force_login(self.view_only_user)
        url = reverse(
            "stacked_inline_hidden_field_on_single_line_admin:"
            "admin_inlines_someparentmodel_change",
            args=(self.parent.pk,),
        )
        response = self.client.get(url)
        # The whole line containing position field is hidden.
        self.assertInHTML(
            '<div class="form-row hidden field-position">'
            '<div class="flex-container"><label>Position:</label>'
            '<div class="help hidden"><div>Position help_text.</div></div>'
            '<div class="readonly">0</div>'
            "</div></div>",
            response.rendered_content,
        )
        self.assertInHTML(
            '<div class="form-row hidden field-position">'
            '<div class="flex-container"><label>Position:</label>'
            '<div class="help hidden"><div>Position help_text.</div></div>'
            '<div class="readonly">1</div>'
            "</div></div>",
            response.rendered_content,
        )
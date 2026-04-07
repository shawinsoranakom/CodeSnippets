def test_stacked_inline_hidden_field_with_view_only_permissions(self):
        """
        Content of hidden field is not visible in stacked inline when user has
        view-only permission.
        """
        self.client.force_login(self.view_only_user)
        url = reverse(
            "stacked_inline_hidden_field_in_group_admin:"
            "admin_inlines_someparentmodel_change",
            args=(self.parent.pk,),
        )
        response = self.client.get(url)
        # The whole line containing name + position fields is not hidden.
        self.assertContains(
            response,
            "<div class="
            '"form-row flex-container form-multiline field-name field-position">',
        )
        # The div containing the position field is hidden.
        self.assertInHTML(
            '<div class="flex-container field-position fieldBox hidden">'
            '<label class="inline">Position:</label>'
            '<div class="help hidden"><div>Position help_text.</div></div>'
            '<div class="readonly">0</div></div>',
            response.rendered_content,
        )
        self.assertInHTML(
            '<div class="flex-container field-position fieldBox hidden">'
            '<label class="inline">Position:</label>'
            '<div class="help hidden"><div>Position help_text.</div></div>'
            '<div class="readonly">1</div></div>',
            response.rendered_content,
        )
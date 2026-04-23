def test_tabular_inline_hidden_field_with_view_only_permissions(self):
        """
        Content of hidden field is not visible in tabular inline when user has
        view-only permission.
        """
        self.client.force_login(self.view_only_user)
        url = reverse(
            "tabular_inline_hidden_field_admin:admin_inlines_someparentmodel_change",
            args=(self.parent.pk,),
        )
        response = self.client.get(url)
        self.assertInHTML(
            '<th class="column-position hidden">Position'
            '<img src="/static/admin/img/icon-unknown.svg" '
            'class="help help-tooltip" width="10" height="10" '
            'alt="(Position help_text.)" '
            'title="Position help_text.">'
            "</th>",
            response.rendered_content,
        )
        self.assertInHTML(
            '<td class="field-position hidden"><p>0</p></td>', response.rendered_content
        )
        self.assertInHTML(
            '<td class="field-position hidden"><p>1</p></td>', response.rendered_content
        )
def test_change_list_boolean_display_property(self):
        response = self.client.get(reverse("admin:admin_views_article_changelist"))
        self.assertContains(
            response,
            '<td class="field-model_property_is_from_past">'
            '<img src="/static/admin/img/icon-yes.svg" alt="True"></td>',
        )
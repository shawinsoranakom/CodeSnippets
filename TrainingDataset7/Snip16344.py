def test_get_sortable_by_no_column(self):
        response = self.client.get(reverse("admin6:admin_views_color_changelist"))
        self.assertContains(response, '<th scope="col" class="column-value">')
        self.assertNotContains(response, '<th scope="col" class="sortable column')
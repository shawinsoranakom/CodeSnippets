def test_get_sortable_by_columns_subset(self):
        response = self.client.get(reverse("admin6:admin_views_actor_changelist"))
        self.assertContains(response, '<th scope="col" class="sortable column-age">')
        self.assertContains(response, '<th scope="col" class="column-name">')
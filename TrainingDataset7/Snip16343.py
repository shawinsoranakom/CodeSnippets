def test_sortable_by_no_column(self):
        expected_not_sortable_fields = ("title", "book")
        response = self.client.get(reverse("admin6:admin_views_chapter_changelist"))
        for field_name in expected_not_sortable_fields:
            self.assertContains(
                response, '<th scope="col" class="column-%s">' % field_name
            )
        self.assertNotContains(response, '<th scope="col" class="sortable column')
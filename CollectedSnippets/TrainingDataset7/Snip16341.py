def test_sortable_by_columns_subset(self):
        expected_sortable_fields = ("date", "callable_year")
        expected_not_sortable_fields = (
            "content",
            "model_year",
            "modeladmin_year",
            "model_year_reversed",
            "section",
        )
        response = self.client.get(reverse("admin6:admin_views_article_changelist"))
        for field_name in expected_sortable_fields:
            self.assertContains(
                response, '<th scope="col" class="sortable column-%s">' % field_name
            )
        for field_name in expected_not_sortable_fields:
            self.assertContains(
                response, '<th scope="col" class="column-%s">' % field_name
            )
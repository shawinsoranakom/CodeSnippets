def test_has_related_field_in_list_display_fk(self):
        """Joins shouldn't be performed for <FK>_id fields in list display."""
        state = State.objects.create(name="Karnataka")
        City.objects.create(state=state, name="Bangalore")
        response = self.client.get(reverse("admin:admin_views_city_changelist"), {})

        response.context["cl"].list_display = ["id", "name", "state"]
        self.assertIs(response.context["cl"].has_related_field_in_list_display(), True)

        response.context["cl"].list_display = ["id", "name", "state_id"]
        self.assertIs(response.context["cl"].has_related_field_in_list_display(), False)
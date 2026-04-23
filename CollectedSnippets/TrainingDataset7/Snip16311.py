def test_has_related_field_in_list_display_o2o(self):
        """Joins shouldn't be performed for <O2O>_id fields in list display."""
        media = Media.objects.create(name="Foo")
        Vodcast.objects.create(media=media)
        response = self.client.get(reverse("admin:admin_views_vodcast_changelist"), {})

        response.context["cl"].list_display = ["media"]
        self.assertIs(response.context["cl"].has_related_field_in_list_display(), True)

        response.context["cl"].list_display = ["media_id"]
        self.assertIs(response.context["cl"].has_related_field_in_list_display(), False)
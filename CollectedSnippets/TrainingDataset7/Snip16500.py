def test_list_editable_popup(self):
        """
        Fields should not be list-editable in popups.
        """
        response = self.client.get(reverse("admin:admin_views_person_changelist"))
        self.assertNotEqual(response.context["cl"].list_editable, ())
        response = self.client.get(
            reverse("admin:admin_views_person_changelist") + "?%s" % IS_POPUP_VAR
        )
        self.assertEqual(response.context["cl"].list_editable, ())
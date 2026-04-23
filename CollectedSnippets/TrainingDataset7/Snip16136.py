def test_model_admin_default_delete_action_no_change_url(self):
        """
        The default delete action doesn't break if a ModelAdmin removes the
        change_view URL (#20640).
        """
        obj = UnchangeableObject.objects.create()
        action_data = {
            ACTION_CHECKBOX_NAME: obj.pk,
            "action": "delete_selected",
            "index": "0",
        }
        response = self.client.post(
            reverse("admin:admin_views_unchangeableobject_changelist"), action_data
        )
        # No 500 caused by NoReverseMatch. The page doesn't display a link to
        # the nonexistent change page.
        self.assertContains(
            response, "<li>Unchangeable object: %s</li>" % obj, 1, html=True
        )
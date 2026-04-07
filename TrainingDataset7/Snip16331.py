def test_change_view_with_show_delete_extra_context(self):
        """
        The 'show_delete' context variable in the admin's change view controls
        the display of the delete button.
        """
        instance = UndeletableObject.objects.create(name="foo")
        response = self.client.get(
            reverse("admin:admin_views_undeletableobject_change", args=(instance.pk,))
        )
        self.assertNotContains(response, "deletelink")
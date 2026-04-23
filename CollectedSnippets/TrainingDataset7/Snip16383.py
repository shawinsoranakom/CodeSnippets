def test_save_as_new_with_validation_errors_with_inlines(self):
        parent = Parent.objects.create(name="Father")
        child = Child.objects.create(parent=parent, name="Child")
        response = self.client.post(
            reverse("admin:admin_views_parent_change", args=(parent.pk,)),
            {
                "_saveasnew": "Save as new",
                "child_set-0-parent": parent.pk,
                "child_set-0-id": child.pk,
                "child_set-0-name": "Child",
                "child_set-INITIAL_FORMS": 1,
                "child_set-MAX_NUM_FORMS": 1000,
                "child_set-MIN_NUM_FORMS": 0,
                "child_set-TOTAL_FORMS": 4,
                "name": "_invalid",
            },
        )
        self.assertContains(response, "Please correct the error below.")
        self.assertFalse(response.context["show_save_and_add_another"])
        self.assertFalse(response.context["show_save_and_continue"])
        self.assertTrue(response.context["show_save_as_new"])
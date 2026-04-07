def test_extended_bodyclass_template_delete_selected_confirmation(self):
        """
        The admin/delete_selected_confirmation.html template uses
        block.super in bodyclass block.
        """
        group = Group.objects.create(name="foogroup")
        post_data = {
            "action": "delete_selected",
            "selected_across": "0",
            "index": "0",
            "_selected_action": group.id,
        }
        response = self.client.post(reverse("admin:auth_group_changelist"), post_data)
        self.assertEqual(response.context["site_header"], "Django administration")
        self.assertContains(response, "bodyclass_consistency_check ")
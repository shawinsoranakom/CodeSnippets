def test_extended_bodyclass_template_delete_confirmation(self):
        """
        The admin/delete_confirmation.html template uses
        block.super in the bodyclass block.
        """
        group = Group.objects.create(name="foogroup")
        response = self.client.get(reverse("admin:auth_group_delete", args=(group.id,)))
        self.assertContains(response, "bodyclass_consistency_check ")
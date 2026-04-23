def test_get_action(self):
        """AdminSite.get_action() returns an action even if it's disabled."""
        action_name = "delete_selected"
        self.assertEqual(self.site.get_action(action_name), delete_selected)
        self.site.disable_action(action_name)
        self.assertEqual(self.site.get_action(action_name), delete_selected)
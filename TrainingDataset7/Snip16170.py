def test_disable_action(self):
        action_name = "delete_selected"
        self.assertEqual(self.site._actions[action_name], delete_selected)
        self.site.disable_action(action_name)
        with self.assertRaises(KeyError):
            self.site._actions[action_name]
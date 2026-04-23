def test_add_action(self):
        def test_action():
            pass

        self.site.add_action(test_action)
        self.assertEqual(self.site.get_action("test_action"), test_action)
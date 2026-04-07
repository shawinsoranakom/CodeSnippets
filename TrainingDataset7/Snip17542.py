def test_get_all_permissions(self):
        self.assertEqual(self.user1.get_all_permissions(TestObj()), {"simple"})
        self.assertEqual(
            self.user2.get_all_permissions(TestObj()), {"simple", "advanced"}
        )
        self.assertEqual(self.user2.get_all_permissions(), set())
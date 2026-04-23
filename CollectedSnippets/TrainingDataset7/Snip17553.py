def test_get_all_permissions(self):
        self.assertEqual(self.user1.get_all_permissions(TestObj()), {"anon"})
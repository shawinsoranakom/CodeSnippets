def test_get_parent_list(self):
        self.assertEqual(Child._meta.get_parent_list(), list(Child._meta.all_parents))
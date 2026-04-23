def test_list(self):
        self.assertEqual(get_hash([1, 2]), get_hash([1, 2]))
        self.assertNotEqual(get_hash([1, 2]), get_hash([2, 2]))
        self.assertNotEqual(get_hash([1]), get_hash(1))

        # test that we can hash self-referencing lists
        a = [1, 2, 3]
        a.append(a)
        b = [1, 2, 3]
        b.append(b)
        self.assertEqual(get_hash(a), get_hash(b))
def test_reverse_with_invalid_fragment(self):
        cases = [0, False, {}, [], set(), ()]
        for fragment in cases:
            with self.subTest(fragment=fragment):
                with self.assertRaises(TypeError):
                    reverse("test", fragment=fragment)
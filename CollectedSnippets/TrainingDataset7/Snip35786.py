def test_reverse_with_empty_fragment(self):
        self.assertEqual(reverse("test", fragment=None), "/test/1")
        self.assertEqual(reverse("test", fragment=""), "/test/1#")
def test_reverse_with_fragment(self):
        self.assertEqual(reverse("test", fragment="tab-1"), "/test/1#tab-1")
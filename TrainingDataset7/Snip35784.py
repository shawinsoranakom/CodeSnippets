def test_reverse_with_fragment_not_encoded(self):
        self.assertEqual(
            reverse("test", fragment="tab 1 is the best!"), "/test/1#tab 1 is the best!"
        )
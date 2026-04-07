def test_lookup_integer_in_charfield(self):
        self.assertEqual(Post.objects.filter(title=9).count(), 0)
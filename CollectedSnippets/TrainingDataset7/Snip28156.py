def test_lookup_integer_in_textfield(self):
        self.assertEqual(Post.objects.filter(body=24).count(), 0)
def test_emoji(self):
        p = Post.objects.create(title="Smile 😀", body="Whatever.")
        p.refresh_from_db()
        self.assertEqual(p.title, "Smile 😀")
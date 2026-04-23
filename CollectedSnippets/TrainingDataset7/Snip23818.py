def test_delete_with_redirect(self):
        res = self.client.post("/edit/author/%s/delete/redirect/" % self.author.pk)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/edit/authors/create/")
        self.assertQuerySetEqual(Author.objects.all(), [])
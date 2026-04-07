def test_delete_by_delete(self):
        # Deletion with browser compatible DELETE method
        res = self.client.delete("/edit/author/%s/delete/" % self.author.pk)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, "/list/authors/")
        self.assertQuerySetEqual(Author.objects.all(), [])
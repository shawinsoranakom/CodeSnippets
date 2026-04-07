def test_nonint_content_type(self):
        an_author = Author.objects.all()[0]
        short_url = "/shortcut/%s/%s/" % ("spam", an_author.pk)
        response = self.client.get(short_url)
        self.assertEqual(response.status_code, 404)
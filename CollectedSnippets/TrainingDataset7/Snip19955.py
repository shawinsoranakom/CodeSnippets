def test_shortcut_bad_pk(self):
        short_url = "/shortcut/%s/%s/" % (
            ContentType.objects.get_for_model(Author).id,
            "42424242",
        )
        response = self.client.get(short_url)
        self.assertEqual(response.status_code, 404)
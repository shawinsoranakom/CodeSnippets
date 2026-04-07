def test_wrong_type_pk(self):
        short_url = "/shortcut/%s/%s/" % (
            ContentType.objects.get_for_model(Author).id,
            "nobody/expects",
        )
        response = self.client.get(short_url)
        self.assertEqual(response.status_code, 404)
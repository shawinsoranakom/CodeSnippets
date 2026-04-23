def test_put(self):
        response = self.client.put("/put_view/", {"foo": "bar"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, "PUT Template")
        self.assertEqual(response.context["data"], "{'foo': 'bar'}")
        self.assertEqual(response.context["Content-Length"], "14")
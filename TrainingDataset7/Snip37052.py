def test_404(self):
        response = self.client.get("/%s/nonexistent_resource" % self.prefix)
        self.assertEqual(404, response.status_code)
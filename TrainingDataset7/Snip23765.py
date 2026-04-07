def test_detail_missing_object(self):
        res = self.client.get("/detail/author/500/")
        self.assertEqual(res.status_code, 404)
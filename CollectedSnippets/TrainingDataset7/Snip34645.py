def test_exc_info_none(self):
        response = self.client.get("/get_view/")
        self.assertIsNone(response.exc_info)
def test_view_with_exception(self):
        "Request a page that is known to throw an error"
        with self.assertRaises(KeyError):
            self.client.get("/broken_view/")
def test_default_handler(self):
        "If the urls.py doesn't specify handlers, the defaults are used"
        response = self.client.get("/test/")
        self.assertEqual(response.status_code, 404)

        msg = "I don't think I'm getting good value for this view"
        with self.assertRaisesMessage(ValueError, msg):
            self.client.get("/bad_view/")
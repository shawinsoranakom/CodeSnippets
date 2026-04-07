def test_no_handler_exception(self):
        msg = (
            "The included URLconf 'None' does not appear to have any patterns "
            "in it. If you see the 'urlpatterns' variable with valid patterns "
            "in the file then the issue is probably caused by a circular "
            "import."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.client.get("/test/me/")
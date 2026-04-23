def test_no_session(self):
        msg = (
            "The session-based temporary message storage requires session "
            "middleware to be installed, and come before the message "
            "middleware in the MIDDLEWARE list."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            self.storage_class(HttpRequest())
def test_sanitize_address_deprecated(self):
        msg = (
            "The internal API sanitize_address() is deprecated."
            " Python's modern email API (with email.message.EmailMessage or"
            " email.policy.default) will handle most required validation and"
            " encoding. Use Python's email.headerregistry.Address to construct"
            " formatted addresses from component parts."
        )
        with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
            sanitize_address("to@example.com", "ascii")
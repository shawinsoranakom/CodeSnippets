def test_decode_failure_logged_to_security(self):
        tests = [
            base64.b64encode(b"flaskdj:alkdjf").decode("ascii"),
            "bad:encoded:value",
        ]
        for encoded in tests:
            with self.subTest(encoded=encoded):
                with self.assertLogs(
                    "django.security.SuspiciousSession", "WARNING"
                ) as cm:
                    self.assertEqual(self.session.decode(encoded), {})
                # The failed decode is logged.
                self.assertIn("Session data corrupted", cm.output[0])
def verify_unsafe_email(self, view, check_for_POST_params=True):
        """
        Asserts that potentially sensitive info are displayed in the email
        report.
        """
        with self.settings(ADMINS=["admin@example.com"]):
            mail.outbox = []  # Empty outbox
            request = self.rf.post("/some_url/", self.breakfast_data)
            if iscoroutinefunction(view):
                async_to_sync(view)(request)
            else:
                view(request)
            self.assertEqual(len(mail.outbox), 1)
            email = mail.outbox[0]

            # Frames vars are never shown in plain text email reports.
            body_plain = str(email.body)
            self.assertNotIn("cooked_eggs", body_plain)
            self.assertNotIn("scrambled", body_plain)
            self.assertNotIn("sauce", body_plain)
            self.assertNotIn("worcestershire", body_plain)

            # Frames vars are shown in html email reports.
            body_html = str(email.alternatives[0].content)
            self.assertIn("cooked_eggs", body_html)
            self.assertIn("scrambled", body_html)
            self.assertIn("sauce", body_html)
            self.assertIn("worcestershire", body_html)

            if check_for_POST_params:
                for k, v in self.breakfast_data.items():
                    # All POST parameters are shown.
                    self.assertIn(k, body_plain)
                    self.assertIn(v, body_plain)
                    self.assertIn(k, body_html)
                    self.assertIn(v, body_html)
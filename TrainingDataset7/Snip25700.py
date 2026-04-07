def test_disallowed_host_doesnt_crash(self):
        admin_email_handler = self.get_admin_email_handler(self.logger)
        old_include_html = admin_email_handler.include_html

        # Text email
        admin_email_handler.include_html = False
        try:
            self.client.get("/", headers={"host": "evil.com"})
        finally:
            admin_email_handler.include_html = old_include_html

        # HTML email
        admin_email_handler.include_html = True
        try:
            self.client.get("/", headers={"host": "evil.com"})
        finally:
            admin_email_handler.include_html = old_include_html
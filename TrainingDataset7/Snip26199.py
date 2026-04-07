def test_empty_admins(self):
        """
        mail_admins/mail_managers doesn't connect to the mail server
        if there are no recipients (#9383)
        """
        for mail_func in [mail_managers, mail_admins]:
            with self.subTest(mail_func=mail_func):
                mail_func("hi", "there")
                self.assertEqual(self.get_mailbox_content(), [])
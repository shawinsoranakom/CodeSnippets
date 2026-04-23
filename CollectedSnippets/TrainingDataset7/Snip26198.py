def test_manager_and_admin_mail_prefix(self):
        """
        String prefix + lazy translated subject = bad output
        Regression for #13494
        """
        for mail_func in [mail_managers, mail_admins]:
            with self.subTest(mail_func=mail_func):
                mail_func(gettext_lazy("Subject"), "Content")
                message = self.get_the_message()
                self.assertEqual(message.get("subject"), "[Django] Subject")
                self.flush_mailbox()
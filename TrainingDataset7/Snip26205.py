def test_lazy_addresses(self):
        """
        Email sending should support lazy email addresses (#24416).
        """
        _ = gettext_lazy
        self.assertTrue(send_mail("Subject", "Content", _("tester"), [_("django")]))
        message = self.get_the_message()
        self.assertEqual(message.get("from"), "tester")
        self.assertEqual(message.get("to"), "django")

        self.flush_mailbox()
        m = EmailMessage(
            from_email=_("tester"),
            to=[_("to1"), _("to2")],
            cc=[_("cc1"), _("cc2")],
            bcc=[_("bcc")],
            reply_to=[_("reply")],
        )
        self.assertEqual(m.recipients(), ["to1", "to2", "cc1", "cc2", "bcc"])
        m.send()
        message = self.get_the_message()
        self.assertEqual(message.get("from"), "tester")
        self.assertEqual(message.get("to"), "to1, to2")
        self.assertEqual(message.get("cc"), "cc1, cc2")
        self.assertEqual(message.get("Reply-To"), "reply")
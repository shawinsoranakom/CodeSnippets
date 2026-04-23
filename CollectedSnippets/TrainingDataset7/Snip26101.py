def test_lazy_headers(self):
        message = EmailMessage(
            subject=gettext_lazy("subject"),
            headers={"List-Unsubscribe": gettext_lazy("list-unsubscribe")},
        ).message()
        self.assertEqual(message.get_all("Subject"), ["subject"])
        self.assertEqual(message.get_all("List-Unsubscribe"), ["list-unsubscribe"])
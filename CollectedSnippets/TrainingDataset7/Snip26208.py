def get_mailbox_content(self):
        return [m.message() for m in mail.outbox]
def flush_mailbox(self):
        mail.outbox = []
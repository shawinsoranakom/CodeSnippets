def flush_mailbox(self):
        self.mailbox[:] = []
        self.smtp_envelopes[:] = []
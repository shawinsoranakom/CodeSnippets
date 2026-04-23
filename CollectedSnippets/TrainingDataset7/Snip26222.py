def flush_mailbox(self):
        self.stream = sys.stdout = StringIO()
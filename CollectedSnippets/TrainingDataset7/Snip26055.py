def send_messages(self, email_messages):
        # Messages are stored in an instance variable for testing.
        self.test_outbox.extend(email_messages)
        return len(email_messages)
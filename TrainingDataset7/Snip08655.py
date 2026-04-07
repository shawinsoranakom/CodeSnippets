def send_messages(self, messages):
        """Redirect messages to the dummy outbox"""
        msg_count = 0
        for message in messages:  # .message() triggers header validation
            message.message()
            mail.outbox.append(copy.deepcopy(message))
            msg_count += 1
        return msg_count
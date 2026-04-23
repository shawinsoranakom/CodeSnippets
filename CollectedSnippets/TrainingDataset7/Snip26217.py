def get_mailbox_content(self):
        messages = []
        for filename in os.listdir(self.tmp_dir):
            with open(os.path.join(self.tmp_dir, filename), "rb") as fp:
                session = fp.read().split(b"\n" + (b"-" * 79) + b"\n")
            messages.extend(message_from_bytes(m) for m in session if m)
        return messages
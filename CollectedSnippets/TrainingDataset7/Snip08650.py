def write_message(self, message):
        self.stream.write(message.message().as_bytes() + b"\n")
        self.stream.write(b"-" * 79)
        self.stream.write(b"\n")
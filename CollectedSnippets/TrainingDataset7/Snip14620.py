def feed(self, data):
        try:
            super().feed(data)
        except self.TruncationCompleted:
            self.output.extend([f"</{tag}>" for tag in self.tags])
            self.tags.clear()
            self.reset()
        else:
            # No data was handled.
            self.reset()
def end_serialization(self):
        if self.options.get("indent"):
            self.stream.write("\n")
        self.stream.write("]")
        self.stream.write("\n")
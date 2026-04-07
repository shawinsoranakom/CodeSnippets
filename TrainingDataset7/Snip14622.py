def process(self, data):
        self.processed_chars += len(data)
        if (self.processed_chars == self.length) and (
            sum(len(p) for p in self.output) + len(data) == len(self.rawdata)
        ):
            self.output.append(data)
            raise self.TruncationCompleted
        output = escape("".join(data[: self.remaining]))
        return data, output
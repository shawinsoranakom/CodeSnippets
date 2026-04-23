def process(self, data):
        data = re.split(r"(?<=\S)\s+(?=\S)", data)
        output = escape(" ".join(data[: self.remaining]))
        return data, output
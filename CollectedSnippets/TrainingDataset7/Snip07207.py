def __iter__(self):
        "Iterate over each point in the coordinate sequence."
        for i in range(self.size):
            yield self[i]
def rotate(self, rotation: int) -> None:
    for _ in range(rotation):
        temp = self.stack[0]
        self.stack = self.stack[1:]
        self.put(temp)
        self.length = self.length - 1

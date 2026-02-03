def rotate(self, rotation: int) -> None:
    put = self.entries.append
    get = self.entries.pop

    for _ in range(rotation):
        put(get(0))

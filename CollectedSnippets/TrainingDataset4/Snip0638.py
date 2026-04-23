def insert_many(self, words: list[str]) -> None:
    for word in words:
        self.insert(word)

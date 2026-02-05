def match(self, word: str) -> tuple[str, str, str]:
    x = 0
    for q, w in zip(self.prefix, word):
        if q != w:
            break

        x += 1

    return self.prefix[:x], self.prefix[x:], word[x:]

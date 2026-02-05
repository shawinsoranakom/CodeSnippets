def build_suffix_tree(self) -> None:
    text = self.text
    n = len(text)
    for i in range(n):
        suffix = text[i:]
        self._add_suffix(suffix, i)

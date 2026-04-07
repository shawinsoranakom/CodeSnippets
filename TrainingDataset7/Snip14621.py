def __init__(self, *, length, replacement, convert_charrefs=True):
        self.length = length
        self.processed_chars = 0
        super().__init__(
            length=calculate_truncate_chars_length(length, replacement),
            replacement=replacement,
            convert_charrefs=convert_charrefs,
        )
def __init__(self, *, length, replacement, convert_charrefs=True):
        super().__init__(convert_charrefs=convert_charrefs)
        self.tags = deque()
        self.output = []
        self.remaining = length
        self.replacement = replacement
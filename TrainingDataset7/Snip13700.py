def __init__(self):
        super().__init__()
        self.root = RootElement()
        self.open_tags = []
        self.element_positions = {}
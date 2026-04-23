def __init__(self, name, attributes):
        self.name = name
        self.attributes = sorted(attributes)
        self.children = []
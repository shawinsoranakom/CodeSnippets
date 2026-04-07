def __init__(self, value):
        super().__init__(sorted(value, key=repr))
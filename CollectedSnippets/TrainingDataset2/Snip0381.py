class Node:
    def __init__(self, name, val):
        self.name = name
        self.val = val

    def __str__(self):
        return f"{self.__class__.__name__}({self.name}, {self.val})"

    def __lt__(self, other):
        return self.val < other.val

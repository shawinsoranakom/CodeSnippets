class Node:
    def __init__(self, val):
        self.val = val
        self.left_tree_size = 0
        self.left = None
        self.right = None
        self.parent = None

    def merge_trees(self, other):
        assert self.left_tree_size == other.left_tree_size, "Unequal Sizes of Blocks"

        if self.val < other.val:
            other.left = self.right
            other.parent = None
            if self.right:
                self.right.parent = other
            self.right = other
            self.left_tree_size = self.left_tree_size * 2 + 1
            return self
        else:
            self.left = other.right
            self.parent = None
            if other.right:
                other.right.parent = self
            other.right = self
            other.left_tree_size = other.left_tree_size * 2 + 1
            return other

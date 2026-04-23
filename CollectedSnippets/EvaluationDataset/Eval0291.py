class SegmentTreeNode:
    def __init__(self, start, end, val, left=None, right=None):
        self.start = start
        self.end = end
        self.val = val
        self.mid = (start + end) // 2
        self.left = left
        self.right = right

    def __repr__(self):
        return f"SegmentTreeNode(start={self.start}, end={self.end}, val={self.val})"

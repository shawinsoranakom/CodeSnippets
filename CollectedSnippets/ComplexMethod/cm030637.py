def check_sanity(self):
        super().check_sanity()
        if self.suicided:
            assert self.left is None
            assert self.right is None
        else:
            left = self.left
            if left.suicided:
                assert left.right is None
            else:
                assert left.right is self
            right = self.right
            if right.suicided:
                assert right.left is None
            else:
                assert right.left is self
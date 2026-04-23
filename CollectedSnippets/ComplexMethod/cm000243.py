def _remove_repair(self) -> None:
        """Repair the coloring of the tree that may have been messed up."""
        if (
            self.parent is None
            or self.sibling is None
            or self.parent.sibling is None
            or self.grandparent is None
        ):
            return
        if color(self.sibling) == 1:
            self.sibling.color = 0
            self.parent.color = 1
            if self.is_left():
                self.parent.rotate_left()
            else:
                self.parent.rotate_right()
        if (
            color(self.parent) == 0
            and color(self.sibling) == 0
            and color(self.sibling.left) == 0
            and color(self.sibling.right) == 0
        ):
            self.sibling.color = 1
            self.parent._remove_repair()
            return
        if (
            color(self.parent) == 1
            and color(self.sibling) == 0
            and color(self.sibling.left) == 0
            and color(self.sibling.right) == 0
        ):
            self.sibling.color = 1
            self.parent.color = 0
            return
        if (
            self.is_left()
            and color(self.sibling) == 0
            and color(self.sibling.right) == 0
            and color(self.sibling.left) == 1
        ):
            self.sibling.rotate_right()
            self.sibling.color = 0
            if self.sibling.right:
                self.sibling.right.color = 1
        if (
            self.is_right()
            and color(self.sibling) == 0
            and color(self.sibling.right) == 1
            and color(self.sibling.left) == 0
        ):
            self.sibling.rotate_left()
            self.sibling.color = 0
            if self.sibling.left:
                self.sibling.left.color = 1
        if (
            self.is_left()
            and color(self.sibling) == 0
            and color(self.sibling.right) == 1
        ):
            self.parent.rotate_left()
            self.grandparent.color = self.parent.color
            self.parent.color = 0
            self.parent.sibling.color = 0
        if (
            self.is_right()
            and color(self.sibling) == 0
            and color(self.sibling.left) == 1
        ):
            self.parent.rotate_right()
            self.grandparent.color = self.parent.color
            self.parent.color = 0
            self.parent.sibling.color = 0
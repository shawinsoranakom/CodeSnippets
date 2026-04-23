def remove(self, label: int) -> RedBlackTree:
        """Remove label from this tree."""
        if self.label == label:
            if self.left and self.right:
                # It's easier to balance a node with at most one child,
                # so we replace this node with the greatest one less than
                # it and remove that.
                value = self.left.get_max()
                if value is not None:
                    self.label = value
                    self.left.remove(value)
            else:
                # This node has at most one non-None child, so we don't
                # need to replace
                child = self.left or self.right
                if self.color == 1:
                    # This node is red, and its child is black
                    # The only way this happens to a node with one child
                    # is if both children are None leaves.
                    # We can just remove this node and call it a day.
                    if self.parent:
                        if self.is_left():
                            self.parent.left = None
                        else:
                            self.parent.right = None
                # The node is black
                elif child is None:
                    # This node and its child are black
                    if self.parent is None:
                        # The tree is now empty
                        return RedBlackTree(None)
                    else:
                        self._remove_repair()
                        if self.is_left():
                            self.parent.left = None
                        else:
                            self.parent.right = None
                        self.parent = None
                else:
                    # This node is black and its child is red
                    # Move the child node here and make it black
                    self.label = child.label
                    self.left = child.left
                    self.right = child.right
                    if self.left:
                        self.left.parent = self
                    if self.right:
                        self.right.parent = self
        elif self.label is not None and self.label > label:
            if self.left:
                self.left.remove(label)
        elif self.right:
            self.right.remove(label)
        return self.parent or self
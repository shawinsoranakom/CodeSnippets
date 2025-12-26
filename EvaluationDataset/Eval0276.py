class RedBlackTree:

    def __init__(
        self,
        label: int | None = None,
        color: int = 0,
        parent: RedBlackTree | None = None,
        left: RedBlackTree | None = None,
        right: RedBlackTree | None = None,
    ) -> None:
        self.label = label
        self.parent = parent
        self.left = left
        self.right = right
        self.color = color


    def rotate_left(self) -> RedBlackTree:
        parent = self.parent
        right = self.right
        if right is None:
            return self
        self.right = right.left
        if self.right:
            self.right.parent = self
        self.parent = right
        right.left = self
        if parent is not None:
            if parent.left == self:
                parent.left = right
            else:
                parent.right = right
        right.parent = parent
        return right

    def rotate_right(self) -> RedBlackTree:
        if self.left is None:
            return self
        parent = self.parent
        left = self.left
        self.left = left.right
        if self.left:
            self.left.parent = self
        self.parent = left
        left.right = self
        if parent is not None:
            if parent.right is self:
                parent.right = left
            else:
                parent.left = left
        left.parent = parent
        return left

    def insert(self, label: int) -> RedBlackTree:
        if self.label is None:
            self.label = label
            return self
        if self.label == label:
            return self
        elif self.label > label:
            if self.left:
                self.left.insert(label)
            else:
                self.left = RedBlackTree(label, 1, self)
                self.left._insert_repair()
        elif self.right:
            self.right.insert(label)
        else:
            self.right = RedBlackTree(label, 1, self)
            self.right._insert_repair()
        return self.parent or self

    def _insert_repair(self) -> None:
        if self.parent is None:
            self.color = 0
        elif color(self.parent) == 0:
            self.color = 1
        else:
            uncle = self.parent.sibling
            if color(uncle) == 0:
                if self.is_left() and self.parent.is_right():
                    self.parent.rotate_right()
                    if self.right:
                        self.right._insert_repair()
                elif self.is_right() and self.parent.is_left():
                    self.parent.rotate_left()
                    if self.left:
                        self.left._insert_repair()
                elif self.is_left():
                    if self.grandparent:
                        self.grandparent.rotate_right()
                        self.parent.color = 0
                    if self.parent.right:
                        self.parent.right.color = 1
                else:
                    if self.grandparent:
                        self.grandparent.rotate_left()
                        self.parent.color = 0
                    if self.parent.left:
                        self.parent.left.color = 1
            else:
                self.parent.color = 0
                if uncle and self.grandparent:
                    uncle.color = 0
                    self.grandparent.color = 1
                    self.grandparent._insert_repair()

    def remove(self, label: int) -> RedBlackTree:
        """Remove label from this tree."""
        if self.label == label:
            if self.left and self.right:
                value = self.left.get_max()
                if value is not None:
                    self.label = value
                    self.left.remove(value)
            else:
                child = self.left or self.right
                if self.color == 1:
                    if self.parent:
                        if self.is_left():
                            self.parent.left = None
                        else:
                            self.parent.right = None
                elif child is None:
                    if self.parent is None:
                        return RedBlackTree(None)
                    else:
                        self._remove_repair()
                        if self.is_left():
                            self.parent.left = None
                        else:
                            self.parent.right = None
                        self.parent = None
                else:
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

    def check_color_properties(self) -> bool:
        if self.color:
            print("Property 2")
            return False
        if not self.check_coloring():
            print("Property 4")
            return False
        if self.black_height() is None:
            print("Property 5")
            return False
        return True

    def check_coloring(self) -> bool:
        if self.color == 1 and 1 in (color(self.left), color(self.right)):
            return False
        if self.left and not self.left.check_coloring():
            return False
        return not (self.right and not self.right.check_coloring())

    def black_height(self) -> int | None:
        if self is None or self.left is None or self.right is None:
            return 1
        left = RedBlackTree.black_height(self.left)
        right = RedBlackTree.black_height(self.right)
        if left is None or right is None:
            return None
        if left != right:
            return None
        return left + (1 - self.color)


    def __contains__(self, label: int) -> bool:
        return self.search(label) is not None

    def search(self, label: int) -> RedBlackTree | None:
        if self.label == label:
            return self
        elif self.label is not None and label > self.label:
            if self.right is None:
                return None
            else:
                return self.right.search(label)
        elif self.left is None:
            return None
        else:
            return self.left.search(label)

    def floor(self, label: int) -> int | None:
        if self.label == label:
            return self.label
        elif self.label is not None and self.label > label:
            if self.left:
                return self.left.floor(label)
            else:
                return None
        else:
            if self.right:
                attempt = self.right.floor(label)
                if attempt is not None:
                    return attempt
            return self.label

    def ceil(self, label: int) -> int | None:
        if self.label == label:
            return self.label
        elif self.label is not None and self.label < label:
            if self.right:
                return self.right.ceil(label)
            else:
                return None
        else:
            if self.left:
                attempt = self.left.ceil(label)
                if attempt is not None:
                    return attempt
            return self.label

    def get_max(self) -> int | None:
        if self.right:
            return self.right.get_max()
        else:
            return self.label

    def get_min(self) -> int | None:
        if self.left:
            return self.left.get_min()
        else:
            return self.label

    @property
    def grandparent(self) -> RedBlackTree | None:
        if self.parent is None:
            return None
        else:
            return self.parent.parent

    @property
    def sibling(self) -> RedBlackTree | None:
        if self.parent is None:
            return None
        elif self.parent.left is self:
            return self.parent.right
        else:
            return self.parent.left

    def is_left(self) -> bool:
        if self.parent is None:
            return False
        return self.parent.left is self

    def is_right(self) -> bool:
        if self.parent is None:
            return False
        return self.parent.right is self

    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        ln = 1
        if self.left:
            ln += len(self.left)
        if self.right:
            ln += len(self.right)
        return ln

    def preorder_traverse(self) -> Iterator[int | None]:
        yield self.label
        if self.left:
            yield from self.left.preorder_traverse()
        if self.right:
            yield from self.right.preorder_traverse()

    def inorder_traverse(self) -> Iterator[int | None]:
        if self.left:
            yield from self.left.inorder_traverse()
        yield self.label
        if self.right:
            yield from self.right.inorder_traverse()

    def postorder_traverse(self) -> Iterator[int | None]:
        if self.left:
            yield from self.left.postorder_traverse()
        if self.right:
            yield from self.right.postorder_traverse()
        yield self.label

    def __repr__(self) -> str:
        from pprint import pformat

        if self.left is None and self.right is None:
            return f"'{self.label} {(self.color and 'red') or 'blk'}'"
        return pformat(
            {
                f"{self.label} {(self.color and 'red') or 'blk'}": (
                    self.left,
                    self.right,
                )
            },
            indent=1,
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RedBlackTree):
            return NotImplemented
        if self.label == other.label:
            return self.left == other.left and self.right == other.right
        else:
            return False

class RandomizedHeapNode[T: bool]:

    def __init__(self, value: T) -> None:
        self._value: T = value
        self.left: RandomizedHeapNode[T] | None = None
        self.right: RandomizedHeapNode[T] | None = None

    @property
    def value(self) -> T:
        return self._value

    @staticmethod
    def merge(
        root1: RandomizedHeapNode[T] | None, root2: RandomizedHeapNode[T] | None
    ) -> RandomizedHeapNode[T] | None:
        if not root1:
            return root2

        if not root2:
            return root1

        if root1.value > root2.value:
            root1, root2 = root2, root1

        if random.choice([True, False]):
            root1.left, root1.right = root1.right, root1.left

        root1.left = RandomizedHeapNode.merge(root1.left, root2)

        return root1

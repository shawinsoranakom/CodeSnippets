class KDNode:

    def __init__(
        self,
        point: list[float],
        left: KDNode | None = None,
        right: KDNode | None = None,
    ) -> None:
        self.point = point
        self.left = left
        self.right = right

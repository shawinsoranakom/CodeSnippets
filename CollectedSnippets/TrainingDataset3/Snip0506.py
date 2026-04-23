class SkipList[KT, VT]:
    def __init__(self, p: float = 0.5, max_level: int = 16):
        self.head: Node[KT, VT] = Node[KT, VT]()
        self.level = 0
        self.p = p
        self.max_level = max_level

    def __str__(self) -> str:

        items = list(self)

        if len(items) == 0:
            return f"SkipList(level={self.level})"

        label_size = max((len(str(item)) for item in items), default=4)
        label_size = max(label_size, 4) + 4

        node = self.head
        lines = []

        forwards = node.forward.copy()
        lines.append(f"[{node.key}]".ljust(label_size, "-") + "* " * len(forwards))
        lines.append(" " * label_size + "| " * len(forwards))

        while len(node.forward) != 0:
            node = node.forward[0]

            lines.append(
                f"[{node.key}]".ljust(label_size, "-")
                + " ".join(str(n.key) if n.key == node.key else "|" for n in forwards)
            )
            lines.append(" " * label_size + "| " * len(forwards))
            forwards[: node.level] = node.forward

        lines.append("None".ljust(label_size) + "* " * len(forwards))
        return f"SkipList(level={self.level})\n" + "\n".join(lines)

    def __iter__(self):
        node = self.head

        while len(node.forward) != 0:
            yield node.forward[0].key
            node = node.forward[0]

    def random_level(self) -> int:

        level = 1
        while random() < self.p and level < self.max_level:
            level += 1

        return level

    def _locate_node(self, key) -> tuple[Node[KT, VT] | None, list[Node[KT, VT]]]:
        update_vector = []

        node = self.head

        for i in reversed(range(self.level)):
            while i < node.level and node.forward[i].key < key:
                node = node.forward[i]
            update_vector.append(node)

        update_vector.reverse() 
        if len(node.forward) != 0 and node.forward[0].key == key:
            return node.forward[0], update_vector
        else:
            return None, update_vector

    def delete(self, key: KT):
        node, update_vector = self._locate_node(key)

        if node is not None:
            for i, update_node in enumerate(update_vector):
                if update_node.level > i and update_node.forward[i].key == key:
                    if node.level > i:
                        update_node.forward[i] = node.forward[i]
                    else:
                        update_node.forward = update_node.forward[:i]

    def insert(self, key: KT, value: VT):

        node, update_vector = self._locate_node(key)
        if node is not None:
            node.value = value
        else:
            level = self.random_level()

            if level > self.level:
                for _ in range(self.level - 1, level):
                    update_vector.append(self.head)
                self.level = level

            new_node = Node(key, value)

            for i, update_node in enumerate(update_vector[:level]):
                if update_node.level > i:
                    new_node.forward.append(update_node.forward[i])

                if update_node.level < i + 1:
                    update_node.forward.append(new_node)
                else:
                    update_node.forward[i] = new_node

    def find(self, key: VT) -> VT | None:

        node, _ = self._locate_node(key)

        if node is not None:
            return node.value

        return None

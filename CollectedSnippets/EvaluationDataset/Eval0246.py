def floor_ceiling(root: Node | None, key: int) -> tuple[int | None, int | None]:
    floor_val = None
    ceiling_val = None

    while root:
        if root.key == key:
            floor_val = root.key
            ceiling_val = root.key
            break

        if key < root.key:
            ceiling_val = root.key
            root = root.left
        else:
            floor_val = root.key
            root = root.right

    return floor_val, ceiling_val

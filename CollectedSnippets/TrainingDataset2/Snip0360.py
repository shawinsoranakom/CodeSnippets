def find_set(x: Node) -> Node:
    if x != x.parent:
        x.parent = find_set(x.parent)
    return x.parent

def clone_graph(node: Node | None) -> Node | None:
    if not node:
        return None

    originals_to_clones = {}  
    stack = [node]

    while stack:
        original = stack.pop()

        if original in originals_to_clones:
            continue

        originals_to_clones[original] = Node(original.value)

        stack.extend(original.neighbors or [])

    for original, clone in originals_to_clones.items():
        for neighbor in original.neighbors or []:
            cloned_neighbor = originals_to_clones[neighbor]

            if not clone.neighbors:
                clone.neighbors = []

            clone.neighbors.append(cloned_neighbor)

    return originals_to_clones[node]

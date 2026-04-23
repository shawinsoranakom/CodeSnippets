def level_order(root: Node | None) -> Generator[int]:

    if root is None:
        return

    process_queue = deque([root])

    while process_queue:
        node = process_queue.popleft()
        yield node.data

        if node.left:
            process_queue.append(node.left)
        if node.right:
            process_queue.append(node.right)

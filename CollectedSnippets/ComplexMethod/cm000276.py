def level_order_actual(node: TreeNode) -> None:
    """
    >>> root = TreeNode(1)
    >>> tree_node2 = TreeNode(2)
    >>> tree_node3 = TreeNode(3)
    >>> tree_node4 = TreeNode(4)
    >>> tree_node5 = TreeNode(5)
    >>> tree_node6 = TreeNode(6)
    >>> tree_node7 = TreeNode(7)
    >>> root.left, root.right = tree_node2, tree_node3
    >>> tree_node2.left, tree_node2.right = tree_node4 , tree_node5
    >>> tree_node3.left, tree_node3.right = tree_node6 , tree_node7
    >>> level_order_actual(root)
    1,
    2,3,
    4,5,6,7,
    """
    if not isinstance(node, TreeNode) or not node:
        return
    q: queue.Queue = queue.Queue()
    q.put(node)
    while not q.empty():
        list_ = []
        while not q.empty():
            node_dequeued = q.get()
            print(node_dequeued.data, end=",")
            if node_dequeued.left:
                list_.append(node_dequeued.left)
            if node_dequeued.right:
                list_.append(node_dequeued.right)
        print()
        for inner_node in list_:
            q.put(inner_node)
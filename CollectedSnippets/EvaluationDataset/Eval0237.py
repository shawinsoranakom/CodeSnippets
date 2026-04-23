def binary_tree_top_side_view(root: TreeNode) -> list[int]:

    def breadth_first_search(root: TreeNode, top_view: list[int]) -> None:
        queue = [(root, 0)]
        lookup = defaultdict(list)

        while queue:
            first = queue.pop(0)
            node, hd = first

            lookup[hd].append(node.val)

            if node.left:
                queue.append((node.left, hd - 1))
            if node.right:
                queue.append((node.right, hd + 1))

        for pair in sorted(lookup.items(), key=lambda each: each[0]):
            top_view.append(pair[1][0])

    top_view: list = []
    if not root:
        return top_view

    breadth_first_search(root, top_view)
    return top_view

def merge_two_binary_trees(tree1: Node | None, tree2: Node | None) -> Node | None:
    if tree1 is None:
        return tree2
    if tree2 is None:
        return tree1

    tree1.value = tree1.value + tree2.value
    tree1.left = merge_two_binary_trees(tree1.left, tree2.left)
    tree1.right = merge_two_binary_trees(tree1.right, tree2.right)
    return tree1

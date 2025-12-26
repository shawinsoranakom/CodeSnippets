def is_symmetric_tree(tree: Node) -> bool:
    if tree:
        return is_mirror(tree.left, tree.right)
    return True 

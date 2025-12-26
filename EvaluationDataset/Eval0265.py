def print_preorder(root: Node | None) -> None:
    if root:
        print(root.value)
        print_preorder(root.left)
        print_preorder(root.right)

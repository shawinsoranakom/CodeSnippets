def inorder(root: Node | None) -> None:
    if not root:
        return
    else:
        inorder(root.left)
        print(root.value, end=",")
        inorder(root.right)

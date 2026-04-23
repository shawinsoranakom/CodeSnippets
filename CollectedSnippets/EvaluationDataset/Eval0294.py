def deserialize(data: str) -> TreeNode | None:

    if not data:
        raise ValueError("Data cannot be empty.")

    nodes = data.split(",")

    def build_tree() -> TreeNode | None:
        value = nodes.pop(0)

        if value == "null":
            return None

        node = TreeNode(int(value))
        node.left = build_tree() 
        node.right = build_tree() 
        return node

    return build_tree()

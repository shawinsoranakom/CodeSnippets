def inorder(curr_node: Node | None) -> list[Node]:
  
    node_list = []
    if curr_node is not None:
        node_list = [*inorder(curr_node.left), curr_node, *inorder(curr_node.right)]
    return node_list

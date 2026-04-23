def insert_node(node: MyNode | None, data: Any) -> MyNode | None:
    if node is None:
        return MyNode(data)
    if data < node.get_data():
        node.set_left(insert_node(node.get_left(), data))
        if (
            get_height(node.get_left()) - get_height(node.get_right()) == 2
        ): 
            left_child = node.get_left()
            assert left_child is not None
            if (
                data < left_child.get_data()
            ):  
                node = right_rotation(node)
            else:
                node = lr_rotation(node)
    else:
        node.set_right(insert_node(node.get_right(), data))
        if get_height(node.get_right()) - get_height(node.get_left()) == 2:
            right_child = node.get_right()
            assert right_child is not None
            if data < right_child.get_data():
                node = rl_rotation(node)
            else:
                node = left_rotation(node)
    h1 = my_max(get_height(node.get_right()), get_height(node.get_left())) + 1
    node.set_height(h1)
    return node

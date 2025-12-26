def del_node(root: MyNode, data: Any) -> MyNode | None:
    left_child = root.get_left()
    right_child = root.get_right()
    if root.get_data() == data:
        if left_child is not None and right_child is not None:
            temp_data = get_left_most(right_child)
            root.set_data(temp_data)
            root.set_right(del_node(right_child, temp_data))
        elif left_child is not None:
            root = left_child
        elif right_child is not None:
            root = right_child
        else:
            return None
    elif root.get_data() > data:
        if left_child is None:
            print("No such data")
            return root
        else:
            root.set_left(del_node(left_child, data))
    elif right_child is None:
        return root
    else:
        root.set_right(del_node(right_child, data))

    left_child = root.get_left()
    right_child = root.get_right()

    if get_height(right_child) - get_height(left_child) == 2:
        assert right_child is not None
        if get_height(right_child.get_right()) > get_height(right_child.get_left()):
            root = left_rotation(root)
        else:
            root = rl_rotation(root)
    elif get_height(right_child) - get_height(left_child) == -2:
        assert left_child is not None
        if get_height(left_child.get_left()) > get_height(left_child.get_right()):
            root = right_rotation(root)
        else:
            root = lr_rotation(root)
    height = my_max(get_height(root.get_right()), get_height(root.get_left())) + 1
    root.set_height(height)
    return root

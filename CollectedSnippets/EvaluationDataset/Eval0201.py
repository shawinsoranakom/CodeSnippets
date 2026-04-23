def get_right_most(root: MyNode) -> Any:
    while True:
        right_child = root.get_right()
        if right_child is None:
            break
        root = right_child
    return root.get_data()

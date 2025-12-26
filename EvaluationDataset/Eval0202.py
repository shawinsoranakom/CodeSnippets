def get_left_most(root: MyNode) -> Any:
    while True:
        left_child = root.get_left()
        if left_child is None:
            break
        root = left_child
    return root.get_data()

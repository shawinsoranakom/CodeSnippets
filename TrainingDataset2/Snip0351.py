def build_tree(arr: list[int]) -> Node | None:
    root = Node(len(arr))
    root.minn, root.maxx = min(arr), max(arr)
    if root.minn == root.maxx:
        return root
    pivot = (root.minn + root.maxx) // 2

    left_arr: list[int] = []
    right_arr: list[int] = []

    for index, num in enumerate(arr):
        if num <= pivot:
            left_arr.append(num)
        else:
            right_arr.append(num)
        root.map_left[index] = len(left_arr)
    root.left = build_tree(left_arr)
    root.right = build_tree(right_arr)
    return root

def binary_tree_mirror_dict(binary_tree_mirror_dictionary: dict, root: int):
    if not root or root not in binary_tree_mirror_dictionary:
        return
    left_child, right_child = binary_tree_mirror_dictionary[root][:2]
    binary_tree_mirror_dictionary[root] = [right_child, left_child]
    binary_tree_mirror_dict(binary_tree_mirror_dictionary, left_child)
    binary_tree_mirror_dict(binary_tree_mirror_dictionary, right_child)

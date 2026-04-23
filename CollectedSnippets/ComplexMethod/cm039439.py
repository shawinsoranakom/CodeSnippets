def recursively_check_children_node_values(node, right_sibling=None):
        if node.is_leaf:
            return
        if right_sibling is not None:
            middle = (node.value + right_sibling.value) / 2
            if monotonic_cst == MonotonicConstraint.POS:
                assert node.left_child.value <= node.right_child.value <= middle
                if not right_sibling.is_leaf:
                    assert (
                        middle
                        <= right_sibling.left_child.value
                        <= right_sibling.right_child.value
                    )
            else:  # NEG
                assert node.left_child.value >= node.right_child.value >= middle
                if not right_sibling.is_leaf:
                    assert (
                        middle
                        >= right_sibling.left_child.value
                        >= right_sibling.right_child.value
                    )

        recursively_check_children_node_values(
            node.left_child, right_sibling=node.right_child
        )
        recursively_check_children_node_values(node.right_child)
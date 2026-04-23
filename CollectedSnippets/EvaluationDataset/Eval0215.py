def binary_search_tree_example() -> None:
    t = BinarySearchTree()
    t.put(8)
    t.put(3)
    t.put(6)
    t.put(1)
    t.put(10)
    t.put(14)
    t.put(13)
    t.put(4)
    t.put(7)
    t.put(5)

    print(
        """
            8
           / \\
          3   10
         / \\    \\
        1   6    14
           / \\   /
          4   7 13
           \\
            5
        """
    )

    print("Label 6 exists:", t.exists(6))
    print("Label 13 exists:", t.exists(13))
    print("Label -1 exists:", t.exists(-1))
    print("Label 12 exists:", t.exists(12))

    inorder_traversal_nodes = [i.label for i in t.inorder_traversal()]
    print("Inorder traversal:", inorder_traversal_nodes)

    preorder_traversal_nodes = [i.label for i in t.preorder_traversal()]
    print("Preorder traversal:", preorder_traversal_nodes)

    print("Max. label:", t.get_max_label())
    print("Min. label:", t.get_min_label())

    print("\nDeleting elements 13, 10, 8, 3, 6, 14")
    print(
        """
          4
         / \\
        1   7
             \\
              5
        """
    )
    t.remove(13)
    t.remove(10)
    t.remove(8)
    t.remove(3)
    t.remove(6)
    t.remove(14)

    inorder_traversal_nodes = [i.label for i in t.inorder_traversal()]
    print("Inorder traversal after delete:", inorder_traversal_nodes)

    preorder_traversal_nodes = [i.label for i in t.preorder_traversal()]
    print("Preorder traversal after delete:", preorder_traversal_nodes)

    print("Max. label:", t.get_max_label())
    print("Min. label:", t.get_min_label())

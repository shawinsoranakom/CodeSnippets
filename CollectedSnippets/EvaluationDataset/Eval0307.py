def main() -> None:
    root = None
    print(
        "enter numbers to create a tree, + value to add value into treap, "
        "- value to erase all nodes with value. 'q' to quit. "
    )

    args = input()
    while args != "q":
        root = interact_treap(root, args)
        print(root)
        args = input()

    print("good by!")

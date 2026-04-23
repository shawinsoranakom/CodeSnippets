def interact_treap(root: Node | None, args: str) -> Node | None:
    for arg in args.split():
        if arg[0] == "+":
            root = insert(root, int(arg[1:]))

        elif arg[0] == "-":
            root = erase(root, int(arg[1:]))

        else:
            print("Unknown command")

    return root

def main() -> None:
    trees = {"zero": Node(0), "seven": make_tree_seven(), "nine": make_tree_nine()}
    for name, tree in trees.items():
        print(f"      The {name} tree: {tuple(tree)}")
        print(f"Mirror of {name} tree: {tuple(tree.mirror())}")

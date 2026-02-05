def main() -> None:
    root = RadixNode()
    words = "banana bananas bandanas bandana band apple all beast".split()
    root.insert_many(words)

    print("Words:", words)
    print("Tree:")
    root.print_tree()

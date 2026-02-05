def main() -> None:
    text = "monkey banana"
    suffix_tree = SuffixTree(text)

    patterns = ["ana", "ban", "na", "xyz", "mon"]
    for pattern in patterns:
        found = suffix_tree.search(pattern)
        print(f"Pattern '{pattern}' found: {found}")

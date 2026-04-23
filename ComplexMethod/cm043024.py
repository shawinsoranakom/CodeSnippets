def compare_nodes(node1, node2, differences, path="/"):
    """
    Recursively compare two lxml nodes, appending textual differences to `differences`.
    `path` is used to indicate the location in the tree (like an XPath).
    """
    # 1) Compare tag names
    if node1.tag != node2.tag:
        differences.append(f"Tag mismatch at {path}: '{node1.tag}' vs. '{node2.tag}'")
        return

    # 2) Compare attributes
    # By now, they are sorted in normalize_dom()
    attrs1 = list(node1.attrib.items())
    attrs2 = list(node2.attrib.items())
    if attrs1 != attrs2:
        differences.append(
            f"Attribute mismatch at {path}/{node1.tag}: {attrs1} vs. {attrs2}"
        )

    # 3) Compare text (trim or unify whitespace as needed)
    text1 = (node1.text or "").strip()
    text2 = (node2.text or "").strip()
    # Normalize whitespace
    text1 = " ".join(text1.split())
    text2 = " ".join(text2.split())
    if text1 != text2:
        # If you prefer ignoring newlines or multiple whitespace, do a more robust cleanup
        differences.append(
            f"Text mismatch at {path}/{node1.tag}: '{text1}' vs. '{text2}'"
        )

    # 4) Compare number of children
    children1 = list(node1)
    children2 = list(node2)
    if len(children1) != len(children2):
        differences.append(
            f"Child count mismatch at {path}/{node1.tag}: {len(children1)} vs. {len(children2)}"
        )
        return  # If counts differ, no point comparing child by child

    # 5) Recursively compare each child
    for i, (c1, c2) in enumerate(zip(children1, children2)):
        # Build a path for child
        child_path = f"{path}/{node1.tag}[{i}]"
        compare_nodes(c1, c2, differences, child_path)

    # 6) Compare tail text
    tail1 = (node1.tail or "").strip()
    tail2 = (node2.tail or "").strip()
    if tail1 != tail2:
        differences.append(
            f"Tail mismatch after {path}/{node1.tag}: '{tail1}' vs. '{tail2}'"
        )
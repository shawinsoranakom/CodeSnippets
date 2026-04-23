def _are_immediate_sibling_tables(table_a, table_b):
    """Check if two tables are nearby in the DOM with no significant content between.

    Tables may be in different wrapper divs (e.g. page-break divs) — walk
    upward to find the containers, then check siblings between them.
    """
    # Simple case: same parent
    if table_a.parent is table_b.parent:
        node = table_a.next_sibling
        while node is not None and node is not table_b:
            if hasattr(node, "name") and node.name:
                text = node.get_text(strip=True)
                if text and len(text) > 2:
                    return False
            elif isinstance(node, str) and len(node.strip()) > 2:
                return False
            node = node.next_sibling  # type: ignore[assignment]
        return node is table_b

    # Different parents: walk up to find wrapper containers and check
    # that the gap between them contains no significant content.
    # Typical pattern: <div><table17/></div><hr/><div><table18/></div>
    container_a = table_a.parent
    container_b = table_b.parent
    if container_a is None or container_b is None:
        return False
    # Both containers must share the same grandparent
    if container_a.parent is not container_b.parent:
        return False
    # Table must be the last element in its container
    # (no significant content after the table within the div)
    node = table_a.next_sibling
    while node is not None:
        if hasattr(node, "name") and node.name:
            text = node.get_text(strip=True)
            if text and len(text) > 2:
                return False
        elif isinstance(node, str) and len(node.strip()) > 2:
            return False
        node = node.next_sibling  # type: ignore[assignment]
    # Table_b must be the first significant element in its container
    node = table_b.previous_sibling
    while node is not None:
        if hasattr(node, "name") and node.name:
            text = node.get_text(strip=True)
            if text and len(text) > 2:
                return False
        elif isinstance(node, str) and len(node.strip()) > 2:
            return False
        node = node.previous_sibling  # type: ignore[assignment]
    # Check gap between the two containers (page number, hr, etc. are ok)
    node = container_a.next_sibling
    while node is not None and node is not container_b:
        if hasattr(node, "name") and node.name:
            text = node.get_text(strip=True)
            # Allow page numbers, empty divs, <hr> separators
            if node.name == "hr":
                node = node.next_sibling  # type: ignore[assignment]
                continue
            if text and len(text) > 10:
                # Substantial content between containers — not a continuation
                return False
        elif isinstance(node, str) and len(node.strip()) > 10:
            return False
        node = node.next_sibling  # type: ignore[assignment]
    return node is container_b
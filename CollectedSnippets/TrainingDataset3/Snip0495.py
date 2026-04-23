def in_reverse(linked_list: LinkedList) -> str:
    return " <- ".join(str(line) for line in reversed(tuple(linked_list)))

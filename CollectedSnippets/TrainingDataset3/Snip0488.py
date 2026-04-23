def is_palindrome_dict(head: ListNode | None) -> bool:
    if not head or not head.next_node:
        return True
    d: dict[int, list[int]] = {}
    pos = 0
    while head:
        if head.val in d:
            d[head.val].append(pos)
        else:
            d[head.val] = [pos]
        head = head.next_node
        pos += 1
    checksum = pos - 1
    middle = 0
    for v in d.values():
        if len(v) % 2 != 0:
            middle += 1
        else:
            for step, i in enumerate(range(len(v))):
                if v[i] + v[len(v) - 1 - step] != checksum:
                    return False
        if middle > 1:
            return False
    return True


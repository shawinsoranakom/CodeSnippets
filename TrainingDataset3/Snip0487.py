def is_palindrome_stack(head: ListNode | None) -> bool:
    if not head or not head.next_node:
        return True

    slow: ListNode | None = head
    fast: ListNode | None = head
    while fast and fast.next_node:
        fast = fast.next_node.next_node
        slow = slow.next_node if slow else None
    if slow:
        stack = [slow.val]

        while slow.next_node:
            slow = slow.next_node
            stack.append(slow.val)

        cur: ListNode | None = head
        while stack and cur:
            if stack.pop() != cur.val:
                return False
            cur = cur.next_node

    return True

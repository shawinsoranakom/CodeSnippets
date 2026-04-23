def is_palindrome_stack(head: ListNode | None) -> bool:
    """
    Check if a linked list is a palindrome using a stack.

    Args:
        head (ListNode): The head of the linked list.

    Returns:
        bool: True if the linked list is a palindrome, False otherwise.

    Examples:
        >>> is_palindrome_stack(None)
        True

        >>> is_palindrome_stack(ListNode(1))
        True

        >>> is_palindrome_stack(ListNode(1, ListNode(2)))
        False

        >>> is_palindrome_stack(ListNode(1, ListNode(2, ListNode(1))))
        True

        >>> is_palindrome_stack(ListNode(1, ListNode(2, ListNode(2, ListNode(1)))))
        True
    """
    if not head or not head.next_node:
        return True

    # 1. Get the midpoint (slow)
    slow: ListNode | None = head
    fast: ListNode | None = head
    while fast and fast.next_node:
        fast = fast.next_node.next_node
        slow = slow.next_node if slow else None

    # slow will always be defined,
    # adding this check to resolve mypy static check
    if slow:
        stack = [slow.val]

        # 2. Push the second half into the stack
        while slow.next_node:
            slow = slow.next_node
            stack.append(slow.val)

        # 3. Comparison
        cur: ListNode | None = head
        while stack and cur:
            if stack.pop() != cur.val:
                return False
            cur = cur.next_node

    return True
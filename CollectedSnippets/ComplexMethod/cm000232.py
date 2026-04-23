def is_palindrome(head: ListNode | None) -> bool:
    """
    Check if a linked list is a palindrome.

    Args:
        head: The head of the linked list.

    Returns:
        bool: True if the linked list is a palindrome, False otherwise.

    Examples:
        >>> is_palindrome(None)
        True

        >>> is_palindrome(ListNode(1))
        True

        >>> is_palindrome(ListNode(1, ListNode(2)))
        False

        >>> is_palindrome(ListNode(1, ListNode(2, ListNode(1))))
        True

        >>> is_palindrome(ListNode(1, ListNode(2, ListNode(2, ListNode(1)))))
        True
    """
    if not head:
        return True
    # split the list to two parts
    fast: ListNode | None = head.next_node
    slow: ListNode | None = head
    while fast and fast.next_node:
        fast = fast.next_node.next_node
        slow = slow.next_node if slow else None
    if slow:
        # slow will always be defined,
        # adding this check to resolve mypy static check
        second = slow.next_node
        slow.next_node = None  # Don't forget here! But forget still works!
    # reverse the second part
    node: ListNode | None = None
    while second:
        nxt = second.next_node
        second.next_node = node
        node = second
        second = nxt
    # compare two parts
    # second part has the same or one less node
    while node and head:
        if node.val != head.val:
            return False
        node = node.next_node
        head = head.next_node
    return True
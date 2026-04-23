def is_palindrome(head: ListNode | None) -> bool:
    if not head:
        return True
    fast: ListNode | None = head.next_node
    slow: ListNode | None = head
    while fast and fast.next_node:
        fast = fast.next_node.next_node
        slow = slow.next_node if slow else None
    if slow:
        second = slow.next_node
        slow.next_node = None  
    node: ListNode | None = None
    while second:
        nxt = second.next_node
        second.next_node = node
        node = second
        second = nxt
    while node and head:
        if node.val != head.val:
            return False
        node = node.next_node
        head = head.next_node
    return True

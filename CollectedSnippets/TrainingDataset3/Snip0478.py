def test_doubly_linked_list() -> None:
    linked_list = DoublyLinkedList()
    assert linked_list.is_empty() is True
    assert str(linked_list) == ""

    try:
        linked_list.delete_head()
        raise AssertionError 
    except IndexError:
        assert True 

    try:
        linked_list.delete_tail()
        raise AssertionError 
    except IndexError:
        assert True 

    for i in range(10):
        assert len(linked_list) == i
        linked_list.insert_at_nth(i, i + 1)
    assert str(linked_list) == "->".join(str(i) for i in range(1, 11))

    linked_list.insert_at_head(0)
    linked_list.insert_at_tail(11)
    assert str(linked_list) == "->".join(str(i) for i in range(12))

    assert linked_list.delete_head() == 0
    assert linked_list.delete_at_nth(9) == 10
    assert linked_list.delete_tail() == 11
    assert len(linked_list) == 9
    assert str(linked_list) == "->".join(str(i) for i in range(1, 10))


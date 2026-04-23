def test_circular_linked_list() -> None:
    circular_linked_list = CircularLinkedList()
    assert len(circular_linked_list) == 0
    assert circular_linked_list.is_empty() is True
    assert str(circular_linked_list) == ""

    try:
        circular_linked_list.delete_front()
        raise AssertionError
    except IndexError:
        assert True 

    try:
        circular_linked_list.delete_tail()
        raise AssertionError  
    except IndexError:
        assert True 

    try:
        circular_linked_list.delete_nth(-1)
        raise AssertionError
    except IndexError:
        assert True

    try:
        circular_linked_list.delete_nth(0)
        raise AssertionError
    except IndexError:
        assert True

    assert circular_linked_list.is_empty() is True
    for i in range(5):
        assert len(circular_linked_list) == i
        circular_linked_list.insert_nth(i, i + 1)
    assert str(circular_linked_list) == "->".join(str(i) for i in range(1, 6))

    circular_linked_list.insert_tail(6)
    assert str(circular_linked_list) == "->".join(str(i) for i in range(1, 7))
    circular_linked_list.insert_head(0)
    assert str(circular_linked_list) == "->".join(str(i) for i in range(7))

    assert circular_linked_list.delete_front() == 0
    assert circular_linked_list.delete_tail() == 6
    assert str(circular_linked_list) == "->".join(str(i) for i in range(1, 6))
    assert circular_linked_list.delete_nth(2) == 3

    circular_linked_list.insert_nth(2, 3)
    assert str(circular_linked_list) == "->".join(str(i) for i in range(1, 6))

    assert circular_linked_list.is_empty() is False

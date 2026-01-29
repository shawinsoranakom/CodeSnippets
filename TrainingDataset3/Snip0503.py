def test_singly_linked_list_2() -> None:
    test_input = [
        -9,
        100,
        Node(77345112),
        "dlrow olleH",
        7,
        5555,
        0,
        -192.55555,
        "Hello, world!",
        77.9,
        Node(10),
        None,
        None,
        12.20,
    ]
    linked_list = LinkedList()

    for i in test_input:
        linked_list.insert_tail(i)

    assert linked_list.is_empty() is False
    assert (
        str(linked_list)
        == "-9 -> 100 -> Node(77345112) -> dlrow olleH -> 7 -> 5555 -> "
        "0 -> -192.55555 -> Hello, world! -> 77.9 -> Node(10) -> None -> None -> 12.2"
    )

    result = linked_list.delete_head()
    assert result == -9
    assert (
        str(linked_list) == "100 -> Node(77345112) -> dlrow olleH -> 7 -> 5555 -> 0 -> "
        "-192.55555 -> Hello, world! -> 77.9 -> Node(10) -> None -> None -> 12.2"
    )

    result = linked_list.delete_tail()
    assert result == 12.2
    assert (
        str(linked_list) == "100 -> Node(77345112) -> dlrow olleH -> 7 -> 5555 -> 0 -> "
        "-192.55555 -> Hello, world! -> 77.9 -> Node(10) -> None -> None"
    )

    result = linked_list.delete_nth(10)
    assert result is None
    assert (
        str(linked_list) == "100 -> Node(77345112) -> dlrow olleH -> 7 -> 5555 -> 0 -> "
        "-192.55555 -> Hello, world! -> 77.9 -> Node(10) -> None"
    )

    linked_list.insert_head(Node("Hello again, world!"))
    assert (
        str(linked_list)
        == "Node(Hello again, world!) -> 100 -> Node(77345112) -> dlrow olleH -> "
        "7 -> 5555 -> 0 -> -192.55555 -> Hello, world! -> 77.9 -> Node(10) -> None"
    )

    linked_list.insert_tail(None)
    assert (
        str(linked_list)
        == "Node(Hello again, world!) -> 100 -> Node(77345112) -> dlrow olleH -> 7 -> "
        "5555 -> 0 -> -192.55555 -> Hello, world! -> 77.9 -> Node(10) -> None -> None"
    )

    linked_list.reverse()
    assert (
        str(linked_list)
        == "None -> None -> Node(10) -> 77.9 -> Hello, world! -> -192.55555 -> 0 -> "
        "5555 -> 7 -> dlrow olleH -> Node(77345112) -> 100 -> Node(Hello again, world!)"
    )

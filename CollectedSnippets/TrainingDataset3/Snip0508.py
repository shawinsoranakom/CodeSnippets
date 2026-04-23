def test_insert_overrides_existing_value():
    skip_list = SkipList()
    skip_list.insert("Key1", 10)
    skip_list.insert("Key1", 12)

    skip_list.insert("Key5", 7)
    skip_list.insert("Key7", 10)
    skip_list.insert("Key10", 5)

    skip_list.insert("Key7", 7)
    skip_list.insert("Key5", 5)
    skip_list.insert("Key10", 10)

    node = skip_list.head
    all_values = {}
    while node.level != 0:
        node = node.forward[0]
        all_values[node.key] = node.value

    if len(all_values) != 4:
        print()
    assert len(all_values) == 4
    assert all_values["Key1"] == 12
    assert all_values["Key7"] == 7
    assert all_values["Key5"] == 5
    assert all_values["Key10"] == 10

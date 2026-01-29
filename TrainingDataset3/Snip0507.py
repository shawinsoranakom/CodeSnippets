def test_insert():
    skip_list = SkipList()
    skip_list.insert("Key1", 3)
    skip_list.insert("Key2", 12)
    skip_list.insert("Key3", 41)
    skip_list.insert("Key4", -19)

    node = skip_list.head
    all_values = {}
    while node.level != 0:
        node = node.forward[0]
        all_values[node.key] = node.value

    assert len(all_values) == 4
    assert all_values["Key1"] == 3
    assert all_values["Key2"] == 12
    assert all_values["Key3"] == 41
    assert all_values["Key4"] == -19

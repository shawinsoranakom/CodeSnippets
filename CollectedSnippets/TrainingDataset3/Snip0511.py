def test_deleted_items_are_not_founded_by_find_method():
    skip_list = SkipList()

    skip_list.insert("Key1", 12)
    skip_list.insert("V", 13)
    skip_list.insert("X", 14)
    skip_list.insert("Key2", 15)

    skip_list.delete("V")
    skip_list.delete("Key2")

    assert skip_list.find("V") is None
    assert skip_list.find("Key2") is None

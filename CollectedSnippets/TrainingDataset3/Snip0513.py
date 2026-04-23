def test_delete_doesnt_leave_dead_nodes():
    skip_list = SkipList()

    skip_list.insert("Key1", 12)
    skip_list.insert("V", 13)
    skip_list.insert("X", 142)
    skip_list.insert("Key2", 15)

    skip_list.delete("X")

    def traverse_keys(node):
        yield node.key
        for forward_node in node.forward:
            yield from traverse_keys(forward_node)

    assert len(set(traverse_keys(skip_list.head))) == 4


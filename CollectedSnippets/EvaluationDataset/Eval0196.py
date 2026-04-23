def right_rotation(node: MyNode) -> MyNode:

    print("left rotation node:", node.get_data())
    ret = node.get_left()
    assert ret is not None
    node.set_left(ret.get_right())
    ret.set_right(node)
    h1 = my_max(get_height(node.get_right()), get_height(node.get_left())) + 1
    node.set_height(h1)
    h2 = my_max(get_height(ret.get_right()), get_height(ret.get_left())) + 1
    ret.set_height(h2)
    return ret

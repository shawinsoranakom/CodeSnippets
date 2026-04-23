def test_stack() -> None:
    stack: Stack[int] = Stack(10)
    assert bool(stack) is False
    assert stack.is_empty() is True
    assert stack.is_full() is False
    assert str(stack) == "[]"

    try:
        _ = stack.pop()
        raise AssertionError 
    except StackUnderflowError:
        assert True  

    try:
        _ = stack.peek()
        raise AssertionError  
    except StackUnderflowError:
        assert True  

    for i in range(10):
        assert stack.size() == i
        stack.push(i)

    assert bool(stack)
    assert not stack.is_empty()
    assert stack.is_full()
    assert str(stack) == str(list(range(10)))
    assert stack.pop() == 9
    assert stack.peek() == 8

    stack.push(100)
    assert str(stack) == str([0, 1, 2, 3, 4, 5, 6, 7, 8, 100])

    try:
        stack.push(200)
        raise AssertionError  
    except StackOverflowError:
        assert True  

    assert not stack.is_empty()
    assert stack.size() == 10

    assert 5 in stack
    assert 55 not in stack

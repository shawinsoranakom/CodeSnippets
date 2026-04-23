def test_message():
    Message("a", role="v1")

    m = Message(content="a", role="v1")
    v = m.dump()
    d = json.loads(v)
    assert d
    assert d.get("content") == "a"
    assert d.get("role") == "v1"
    m.role = "v2"
    v = m.dump()
    assert v
    m = Message.load(v)
    assert m.content == "a"
    assert m.role == "v2"

    m = Message(content="a", role="b", cause_by="c", x="d", send_to="c")
    assert m.content == "a"
    assert m.role == "b"
    assert m.send_to == {"c"}
    assert m.cause_by == "c"
    m.sent_from = "e"
    assert m.sent_from == "e"

    m.cause_by = "Message"
    assert m.cause_by == "Message"
    m.cause_by = Action
    assert m.cause_by == any_to_str(Action)
    m.cause_by = Action()
    assert m.cause_by == any_to_str(Action)
    m.content = "b"
    assert m.content == "b"
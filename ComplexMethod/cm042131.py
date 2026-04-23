async def test_action_node_one_layer():
    node = ActionNode(key="key-a", expected_type=str, instruction="instruction-b", example="example-c")

    raw_template = node.compile(context="123", schema="raw", mode="auto")
    json_template = node.compile(context="123", schema="json", mode="auto")
    markdown_template = node.compile(context="123", schema="markdown", mode="auto")
    node_dict = node.to_dict()

    assert "123" in raw_template
    assert "instruction" in raw_template

    assert "123" in json_template
    assert "format example" in json_template
    assert "constraint" in json_template
    assert "action" in json_template
    assert "[/" in json_template

    assert "123" in markdown_template
    assert "key-a" in markdown_template

    assert node_dict["key-a"] == "instruction-b"
    assert "key-a" in repr(node)
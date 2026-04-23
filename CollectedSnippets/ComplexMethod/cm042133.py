async def test_action_node_revise():
    key = "Project Name"
    node_a = ActionNode(
        key=key,
        expected_type=str,
        instruction='According to the content of "Original Requirements," name the project using snake case style '
        "with underline, like 'game_2048' or 'simple_crm.",
        example="game_2048",
    )

    with pytest.raises(RuntimeError):
        _ = await node_a.review()

    _ = await node_a.fill(req=None, llm=LLM())
    setattr(node_a.instruct_content, key, "game snake")  # wrong content to revise
    revise_contents = await node_a.revise(revise_mode=ReviseMode.AUTO)
    assert len(revise_contents) == 1
    assert "game_snake" in getattr(node_a.instruct_content, key)

    revise_contents = await node_a.revise(strgy="complex", revise_mode=ReviseMode.AUTO)
    assert len(revise_contents) == 0

    node = ActionNode.from_children(key="WritePRD", nodes=[node_a])
    with pytest.raises(RuntimeError):
        _ = await node.revise()

    _ = await node.fill(req=None, llm=LLM())
    setattr(node.instruct_content, key, "game snake")
    revise_contents = await node.revise(revise_mode=ReviseMode.AUTO)
    assert len(revise_contents) == 1
    assert "game_snake" in getattr(node.instruct_content, key)

    revise_contents = await node.revise(strgy="complex", revise_mode=ReviseMode.AUTO)
    assert len(revise_contents) == 1
    assert "game_snake" in getattr(node.instruct_content, key)
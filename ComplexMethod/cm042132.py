async def test_action_node_review():
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
    setattr(node_a.instruct_content, key, "game snake")  # wrong content to review

    review_comments = await node_a.review(review_mode=ReviewMode.AUTO)
    assert len(review_comments) == 1
    assert list(review_comments.keys())[0] == key

    review_comments = await node_a.review(strgy="complex", review_mode=ReviewMode.AUTO)
    assert len(review_comments) == 0

    node = ActionNode.from_children(key="WritePRD", nodes=[node_a])
    with pytest.raises(RuntimeError):
        _ = await node.review()

    _ = await node.fill(req=None, llm=LLM())

    review_comments = await node.review(review_mode=ReviewMode.AUTO)
    assert len(review_comments) == 1
    assert list(review_comments.keys())[0] == key

    review_comments = await node.review(strgy="complex", review_mode=ReviewMode.AUTO)
    assert len(review_comments) == 1
    assert list(review_comments.keys())[0] == key
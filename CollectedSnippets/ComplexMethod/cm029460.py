async def test_compare_openai_inputs_for_evals_returns_first_difference() -> None:
    response = await compare_openai_inputs_for_evals(
        OpenAIInputCompareRequest(
            left_json=(
                '{"input":[{"role":"system","content":"A"},'
                '{"role":"user","content":"Build dashboard"}]}'
            ),
            right_json=(
                '{"input":[{"role":"system","content":"A"},'
                '{"role":"user","content":"Build landing page"}]}'
            ),
        )
    )

    assert response.common_prefix_items == 1
    assert response.left_item_count == 2
    assert response.right_item_count == 2
    assert response.difference is not None
    assert response.difference.path == "input[1].content"
    assert response.difference.left_value == "Build dashboard"
    assert response.difference.right_value == "Build landing page"
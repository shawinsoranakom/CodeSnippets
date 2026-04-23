async def test_config_traceable_async_handoff() -> None:
    tracer = _create_tracer_with_mocked_client()

    @traceable
    def my_great_great_grandchild_function(a: int) -> int:
        return a + 1

    @RunnableLambda
    def my_great_grandchild_function(a: int) -> int:
        return my_great_great_grandchild_function(a)

    @RunnableLambda
    async def my_grandchild_function(a: int) -> int:
        return my_great_grandchild_function.invoke(a)

    @traceable
    async def my_child_function(a: int) -> int:
        return await my_grandchild_function.ainvoke(a) * 3

    @traceable()
    async def my_function(a: int) -> int:
        return await my_child_function(a)

    async def my_parent_function(a: int) -> int:
        return await my_function(a)

    my_parent_runnable = RunnableLambda(my_parent_function)
    result = await my_parent_runnable.ainvoke(1, {"callbacks": [tracer]})
    assert result == 6
    posts = _get_posts(tracer.client)
    # There should have been 6 runs created,
    # one for each function invocation
    assert len(posts) == 6
    name_to_body = {post["name"]: post for post in posts}
    ordered_names = [
        "my_parent_function",
        "my_function",
        "my_child_function",
        "my_grandchild_function",
        "my_great_grandchild_function",
        "my_great_great_grandchild_function",
    ]
    trace_id = posts[0]["trace_id"]
    last_dotted_order = None
    parent_run_id = None
    for name in ordered_names:
        id_ = name_to_body[name]["id"]
        parent_run_id_ = name_to_body[name].get("parent_run_id")
        if parent_run_id_ is not None:
            assert parent_run_id == parent_run_id_
        assert name in name_to_body
        # All within the same trace
        assert name_to_body[name]["trace_id"] == trace_id
        dotted_order: str = name_to_body[name]["dotted_order"]
        assert dotted_order is not None
        if last_dotted_order is not None:
            assert dotted_order > last_dotted_order
            assert dotted_order.startswith(last_dotted_order), (
                "Unexpected dotted order for run"
                f" {name}\n{dotted_order}\n{last_dotted_order}"
            )
        last_dotted_order = dotted_order
        parent_run_id = id_
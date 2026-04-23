def test_config_traceable_handoff() -> None:
    if hasattr(get_env_var, "cache_clear"):
        get_env_var.cache_clear()  # type: ignore[attr-defined]
    tracer = _create_tracer_with_mocked_client(
        project_name="another-flippin-project", tags=["such-a-tag"]
    )

    @traceable
    def my_great_great_grandchild_function(a: int) -> int:
        rt = get_current_run_tree()
        assert rt
        assert rt.session_name == "another-flippin-project"
        return a + 1

    @RunnableLambda
    def my_great_grandchild_function(a: int) -> int:
        return my_great_great_grandchild_function(a)

    @RunnableLambda
    def my_grandchild_function(a: int) -> int:
        return my_great_grandchild_function.invoke(a)

    @traceable
    def my_child_function(a: int) -> int:
        return my_grandchild_function.invoke(a) * 3

    @traceable()
    def my_function(a: int) -> int:
        rt = get_current_run_tree()
        assert rt
        assert rt.session_name == "another-flippin-project"
        return my_child_function(a)

    def my_parent_function(a: int) -> int:
        rt = get_current_run_tree()
        assert rt
        assert rt.session_name == "another-flippin-project"
        return my_function(a)

    my_parent_runnable = RunnableLambda(my_parent_function)

    assert my_parent_runnable.invoke(1, {"callbacks": [tracer]}) == 6
    posts = _get_posts(tracer.client)
    assert all(post["session_name"] == "another-flippin-project" for post in posts)
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
    assert "such-a-tag" in name_to_body["my_parent_function"]["tags"]
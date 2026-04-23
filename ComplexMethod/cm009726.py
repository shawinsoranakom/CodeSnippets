def test_inheritable_metadata_nested_runs_preserve_parent_child_shape() -> None:
    """Concurrent nested runs keep parent-child linkage within each invocation."""
    tracer = _create_tracer_with_mocked_client()
    barrier = threading.Barrier(2)

    @RunnableLambda
    def child(x: int) -> int:
        barrier.wait()
        return x + 1

    @RunnableLambda
    def parent(x: int) -> int:
        return child.invoke(x)

    def invoke_for_tenant(tenant: str, value: int) -> int:
        callbacks = CallbackManager.configure(
            inheritable_callbacks=[tracer],
            langsmith_inheritable_metadata={"tenant": tenant},
        )
        return parent.invoke(value, {"callbacks": callbacks})

    threads = [
        threading.Thread(target=invoke_for_tenant, args=("alpha", 1)),
        threading.Thread(target=invoke_for_tenant, args=("beta", 2)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    posts = _get_posts(tracer.client)
    assert len(posts) == 4
    parents = [post for post in posts if post["name"] == "parent"]
    children = [post for post in posts if post["name"] == "child"]
    assert len(parents) == 2
    assert len(children) == 2
    parent_ids = {parent["id"] for parent in parents}
    assert {child["parent_run_id"] for child in children} == parent_ids
    assert {
        post.get("extra", {}).get("metadata", {}).get("tenant") for post in posts
    } == {
        "alpha",
        "beta",
    }
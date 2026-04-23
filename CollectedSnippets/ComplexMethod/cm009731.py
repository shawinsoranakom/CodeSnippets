def test_inheritable_metadata_concurrent_invocations_remain_isolated(
        self,
    ) -> None:
        """Parallel invocations through copied tracers keep metadata separated."""
        tracer = _create_tracer_with_mocked_client()
        barrier = threading.Barrier(2)

        @traceable
        def traced_leaf(x: int) -> int:
            barrier.wait()
            return x

        @RunnableLambda
        def my_func(x: int) -> int:
            return traced_leaf(x)

        def invoke_for_tenant(tenant: str, value: int) -> int:
            callbacks = CallbackManager.configure(
                inheritable_callbacks=[tracer],
                langsmith_inheritable_metadata={"tenant": tenant},
            )
            return my_func.invoke(value, {"callbacks": callbacks})

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(invoke_for_tenant, ["alpha", "beta"], [1, 2]))

        posts = _get_posts(tracer.client)
        assert len(posts) == 4
        assert {post["name"] for post in posts} == {"my_func", "traced_leaf"}
        my_func_posts = [post for post in posts if post["name"] == "my_func"]
        assert len(my_func_posts) == 2
        assert {
            post.get("extra", {}).get("metadata", {}).get("tenant")
            for post in my_func_posts
        } == {"alpha", "beta"}
        assert tracer.run_map == {}
        assert len(tracer.order_map) == 2
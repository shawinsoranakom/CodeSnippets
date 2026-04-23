def test_tree_is_constructed(parent_type: Literal["ls", "lc"]) -> None:
    mock_session = MagicMock()
    mock_client_ = Client(
        session=mock_session, api_key="test", auto_batch_tracing=False
    )
    grandchild_run = None
    kitten_run = None

    @traceable
    def kitten(x: str) -> str:
        nonlocal kitten_run
        kitten_run = get_current_run_tree()
        return x

    @RunnableLambda
    def grandchild(x: str) -> str:
        nonlocal grandchild_run
        grandchild_run = get_current_run_tree()
        return kitten(x)

    @RunnableLambda
    def child(x: str) -> str:
        return grandchild.invoke(x)

    rid = uuid.uuid4()
    with tracing_context(
        client=mock_client_,
        enabled=True,
        metadata={"some_foo": "some_bar"},
        tags=["afoo"],
    ):
        collected: dict[str, RunTree] = {}

        def collect_langsmith_run(run: RunTree) -> None:
            collected[str(run.id)] = run

        def collect_tracer_run(_: LangChainTracer, run: RunTree) -> None:
            collected[str(run.id)] = run

        if parent_type == "ls":

            @traceable
            def parent() -> str:
                return child.invoke("foo")

            assert (
                parent(langsmith_extra={"on_end": collect_langsmith_run, "run_id": rid})
                == "foo"
            )
            assert collected

        else:

            @RunnableLambda
            def parent(_: Any) -> str:
                return child.invoke("foo")

            tracer = LangChainTracer()
            with patch.object(LangChainTracer, "_persist_run", new=collect_tracer_run):
                assert (
                    parent.invoke(..., {"run_id": rid, "callbacks": [tracer]}) == "foo"  # type: ignore[attr-defined]
                )
    run = collected.get(str(rid))

    assert run is not None
    assert run.name == "parent"
    assert run.child_runs
    child_run = run.child_runs[0]
    assert child_run.name == "child"
    assert isinstance(grandchild_run, RunTree)
    assert grandchild_run.name == "grandchild"
    assert grandchild_run.metadata.get("some_foo") == "some_bar"
    assert "afoo" in grandchild_run.tags  # type: ignore[operator]
    assert isinstance(kitten_run, RunTree)
    assert kitten_run.name == "kitten"
    assert not kitten_run.child_runs
    assert kitten_run.metadata.get("some_foo") == "some_bar"
    assert "afoo" in kitten_run.tags  # type: ignore[operator]
    assert grandchild_run is not None
    assert kitten_run.dotted_order.startswith(grandchild_run.dotted_order)
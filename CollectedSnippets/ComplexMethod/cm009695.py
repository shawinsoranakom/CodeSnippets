async def test_async_batch_size() -> None:
    llm = FakeListLLM(responses=["foo"] * 3)
    with collect_runs() as cb:
        await llm.abatch(["foo", "bar", "foo"], {"callbacks": [cb]})
        assert all((r.extra or {}).get("batch_size") == 3 for r in cb.traced_runs)
        assert len(cb.traced_runs) == 3
    llm = FakeListLLM(responses=["foo"])
    with collect_runs() as cb:
        await llm.abatch(["foo"], {"callbacks": [cb]})
        assert all((r.extra or {}).get("batch_size") == 1 for r in cb.traced_runs)
        assert len(cb.traced_runs) == 1

    llm = FakeListLLM(responses=["foo"])
    with collect_runs() as cb:
        await llm.ainvoke("foo")
        assert len(cb.traced_runs) == 1
        assert (cb.traced_runs[0].extra or {}).get("batch_size") == 1

    llm = FakeListLLM(responses=["foo"])
    with collect_runs() as cb:
        async for _ in llm.astream("foo"):
            pass
        assert len(cb.traced_runs) == 1
        assert (cb.traced_runs[0].extra or {}).get("batch_size") == 1
async def test_item_only_topology_dispatches_each_row_to_chatoutput():
    """Each row must reach ChatOutput in the loop body when only item is wired."""
    graph, _, _ = _build_item_only_topology(row_count=3)

    queue: asyncio.Queue = asyncio.Queue()
    em = create_default_event_manager(queue=queue)
    results = [r async for r in graph.async_start(event_manager=em)]

    events = await _drain(queue)
    chat_output_runs = [
        d for d in events.get("end_vertex", []) if d.get("build_data", {}).get("id") == "ChatOutput-sink"
    ]
    # 3 rows -> 3 subgraph iterations -> 3 ChatOutput builds.
    assert len(chat_output_runs) == 3, f"ChatOutput should have been built once per row, got {len(chat_output_runs)}"

    # Item inspector surfaces the dispatched inputs wrapped in a Data
    # envelope so the outer item edge remains compatible with Data-typed
    # consumers in the loop body.
    loop_result = next(r for r in results if getattr(r, "vertex", None) and r.vertex.id == "loop")
    item = loop_result.result_dict.outputs["item"]
    assert item["message"]["count"] == 3
    assert [row["text"] for row in item["message"]["items"]] == ["Row 0", "Row 1", "Row 2"]
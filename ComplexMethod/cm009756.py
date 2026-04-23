async def test_stream_log_lists() -> None:
    async def list_producer(_: AsyncIterator[Any]) -> AsyncIterator[AddableDict]:
        for i in range(4):
            yield AddableDict(alist=[str(i)])

    chain = RunnableGenerator(list_producer)

    stream_log = [
        part async for part in chain.astream_log({"question": "What is your name?"})
    ]

    # Remove IDs from logs
    for part in stream_log:
        for op in part.ops:
            if (
                isinstance(op["value"], dict)
                and "id" in op["value"]
                and not isinstance(op["value"]["id"], list)  # serialized lc id
            ):
                del op["value"]["id"]

    assert stream_log == [
        RunLogPatch(
            {
                "op": "replace",
                "path": "",
                "value": {
                    "final_output": None,
                    "logs": {},
                    "streamed_output": [],
                    "name": "list_producer",
                    "type": "chain",
                },
            }
        ),
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": {"alist": ["0"]}},
            {"op": "replace", "path": "/final_output", "value": {"alist": ["0"]}},
        ),
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": {"alist": ["1"]}},
            {"op": "add", "path": "/final_output/alist/1", "value": "1"},
        ),
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": {"alist": ["2"]}},
            {"op": "add", "path": "/final_output/alist/2", "value": "2"},
        ),
        RunLogPatch(
            {"op": "add", "path": "/streamed_output/-", "value": {"alist": ["3"]}},
            {"op": "add", "path": "/final_output/alist/3", "value": "3"},
        ),
    ]

    state = add(stream_log)

    assert isinstance(state, RunLog)

    assert state.state == {
        "final_output": {"alist": ["0", "1", "2", "3"]},
        "logs": {},
        "name": "list_producer",
        "streamed_output": [
            {"alist": ["0"]},
            {"alist": ["1"]},
            {"alist": ["2"]},
            {"alist": ["3"]},
        ],
        "type": "chain",
    }
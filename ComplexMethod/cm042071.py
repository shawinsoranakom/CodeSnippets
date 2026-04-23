async def test_llm_stream_reporter(data, file_path, meta, block, report_cls, http_server):
    async with callback_server(http_server) as (url, callback_data):
        async with report_cls(callback_url=url, enable_llm_stream=True) as reporter:
            await reporter.async_report(meta, "meta")
            await MockFileLLM(data).aask("")
            await reporter.wait_llm_stream_report()
            await reporter.async_report(file_path, "path")
    assert callback_data
    assert all(block is BlockType(i["block"]) for i in callback_data)
    assert all(i["uuid"] == callback_data[0]["uuid"] for i in callback_data[1:])
    chunks, names = [], set()
    for i in callback_data:
        name = i["name"]
        names.add(name)
        if name == "meta":
            assert i["value"] == meta
        elif name == "path":
            assert i["value"] == file_path
        elif name == END_MARKER_NAME:
            pass
        elif name == "content":
            chunks.append(i["value"])
        else:
            raise ValueError
    assert "".join(chunks[:-1]) == data
    assert names == {"meta", "path", "content", END_MARKER_NAME}
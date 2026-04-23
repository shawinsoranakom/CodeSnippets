async def test_notebook_reporter(http_server):
    code = {
        "cell_type": "code",
        "execution_count": None,
        "id": "e1841c44",
        "metadata": {},
        "outputs": [],
        "source": ["\n", "import time\n", "print('will sleep 1s.')\n", "time.sleep(1)\n", "print('end.')\n", ""],
    }
    output1 = {"name": "stdout", "output_type": "stream", "text": ["will sleep 1s.\n"]}
    output2 = {"name": "stdout", "output_type": "stream", "text": ["will sleep 1s.\n"]}
    code_path = "/data/main.ipynb"
    async with callback_server(http_server) as (url, callback_data):
        async with NotebookReporter(callback_url=url) as reporter:
            await reporter.async_report(code, "content")
            await reporter.async_report(output1, "content")
            await reporter.async_report(output2, "content")
            await reporter.async_report(code_path, "path")

    assert all(BlockType.NOTEBOOK is BlockType(i["block"]) for i in callback_data)
    assert len(callback_data) == 5
    assert callback_data[-1]["name"] == END_MARKER_NAME
    assert callback_data[-2]["name"] == "path"
    assert callback_data[-2]["value"] == code_path
    assert all(i["uuid"] == callback_data[0]["uuid"] for i in callback_data[1:])
    assert [i["value"] for i in callback_data if i["name"] == "content"] == [code, output1, output2]
async def test_web_browse_and_summarize(mocker, context):
    async def mock_llm_ask(*args, **kwargs):
        return "metagpt"

    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", mock_llm_ask)
    url = "https://github.com/geekan/MetaGPT"
    url2 = "https://github.com/trending"
    query = "What's new in metagpt"
    resp = await research.WebBrowseAndSummarize(context=context).run(url, query=query)

    assert len(resp) == 1
    assert url in resp
    assert resp[url] == "metagpt"

    resp = await research.WebBrowseAndSummarize(context=context).run(url, url2, query=query)
    assert len(resp) == 2

    async def mock_llm_ask(*args, **kwargs):
        return "Not relevant."

    mocker.patch("metagpt.provider.base_llm.BaseLLM.aask", mock_llm_ask)
    resp = await research.WebBrowseAndSummarize(context=context).run(url, query=query)

    assert len(resp) == 1
    assert url in resp
    assert resp[url] is None
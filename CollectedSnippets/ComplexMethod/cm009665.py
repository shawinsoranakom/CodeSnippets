def test_create_retriever_tool() -> None:
    class MyRetriever(BaseRetriever):
        @override
        def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
        ) -> list[Document]:
            return [Document(page_content=f"foo {query}"), Document(page_content="bar")]

    retriever = MyRetriever()
    retriever_tool = tools.create_retriever_tool(
        retriever, "retriever_tool_content", "Retriever Tool Content"
    )
    assert isinstance(retriever_tool, BaseTool)
    assert retriever_tool.name == "retriever_tool_content"
    assert retriever_tool.description == "Retriever Tool Content"
    assert retriever_tool.invoke("bar") == "foo bar\n\nbar"
    assert retriever_tool.invoke(
        ToolCall(
            name="retriever_tool_content",
            args={"query": "bar"},
            id="123",
            type="tool_call",
        )
    ) == ToolMessage(
        "foo bar\n\nbar", tool_call_id="123", name="retriever_tool_content"
    )

    retriever_tool_artifact = tools.create_retriever_tool(
        retriever,
        "retriever_tool_artifact",
        "Retriever Tool Artifact",
        response_format="content_and_artifact",
    )
    assert isinstance(retriever_tool_artifact, BaseTool)
    assert retriever_tool_artifact.name == "retriever_tool_artifact"
    assert retriever_tool_artifact.description == "Retriever Tool Artifact"
    assert retriever_tool_artifact.invoke("bar") == "foo bar\n\nbar"
    assert retriever_tool_artifact.invoke(
        ToolCall(
            name="retriever_tool_artifact",
            args={"query": "bar"},
            id="123",
            type="tool_call",
        )
    ) == ToolMessage(
        "foo bar\n\nbar",
        artifact=[Document(page_content="foo bar"), Document(page_content="bar")],
        tool_call_id="123",
        name="retriever_tool_artifact",
    )
def _check_response(response: BaseMessage | None) -> None:
    assert isinstance(response, AIMessage)
    assert isinstance(response.content, list)
    for block in response.content:
        assert isinstance(block, dict)
        if block["type"] == "text":
            assert isinstance(block.get("text"), str)
            annotations = block.get("annotations", [])
            for annotation in annotations:
                if annotation["type"] == "file_citation":
                    assert all(
                        key in annotation
                        for key in ["file_id", "filename", "file_index", "type"]
                    )
                elif annotation["type"] == "web_search":
                    assert all(
                        key in annotation
                        for key in ["end_index", "start_index", "title", "type", "url"]
                    )
                elif annotation["type"] == "citation":
                    assert all(key in annotation for key in ["title", "type"])
                    if "url" in annotation:
                        assert "start_index" in annotation
                        assert "end_index" in annotation
    text_content = response.text  # type: ignore[operator,misc]
    assert isinstance(text_content, str)
    assert text_content
    assert response.usage_metadata
    assert response.usage_metadata["input_tokens"] > 0
    assert response.usage_metadata["output_tokens"] > 0
    assert response.usage_metadata["total_tokens"] > 0
    assert response.response_metadata["model_name"]
    assert response.response_metadata["service_tier"]
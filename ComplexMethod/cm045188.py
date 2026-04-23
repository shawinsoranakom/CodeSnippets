def test_mcp_tool_adapter_normalize_payload(sample_tool: Tool, sample_server_params: StdioServerParams) -> None:
    """Test the _normalize_payload_to_content_list method of McpToolAdapter."""
    adapter = StdioMcpToolAdapter(server_params=sample_server_params, tool=sample_tool)

    # Case 1: Payload is already a list of valid content items
    valid_content_list: list[TextContent | ImageContent | EmbeddedResource] = [
        TextContent(text="hello", type="text"),
        ImageContent(data="base64data", mimeType="image/png", type="image"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(text="embedded text", uri=AnyUrl(url="http://example.com/resource")),
        ),
    ]
    assert adapter._normalize_payload_to_content_list(valid_content_list) == valid_content_list  # type: ignore[reportPrivateUsage]

    # Case 2: Payload is a single TextContent
    single_text_content = TextContent(text="single text", type="text")
    assert adapter._normalize_payload_to_content_list(single_text_content) == [single_text_content]  # type: ignore[reportPrivateUsage, arg-type]

    # Case 3: Payload is a single ImageContent
    single_image_content = ImageContent(data="imagedata", mimeType="image/jpeg", type="image")
    assert adapter._normalize_payload_to_content_list(single_image_content) == [single_image_content]  # type: ignore[reportPrivateUsage, arg-type]

    # Case 4: Payload is a single EmbeddedResource
    single_embedded_resource = EmbeddedResource(
        type="resource",
        resource=TextResourceContents(text="other embedded", uri=AnyUrl(url="http://example.com/other")),
    )
    assert adapter._normalize_payload_to_content_list(single_embedded_resource) == [single_embedded_resource]  # type: ignore[reportPrivateUsage, arg-type]

    # Case 5: Payload is a string
    string_payload = "This is a string payload."
    expected_from_string = [TextContent(text=string_payload, type="text")]
    assert adapter._normalize_payload_to_content_list(string_payload) == expected_from_string  # type: ignore[reportPrivateUsage, arg-type]

    # Case 6: Payload is an integer
    int_payload = 12345
    expected_from_int = [TextContent(text=str(int_payload), type="text")]
    assert adapter._normalize_payload_to_content_list(int_payload) == expected_from_int  # type: ignore[reportPrivateUsage, arg-type]

    # Case 7: Payload is a dictionary
    dict_payload = {"key": "value", "number": 42}
    expected_from_dict = [TextContent(text=str(dict_payload), type="text")]
    assert adapter._normalize_payload_to_content_list(dict_payload) == expected_from_dict  # type: ignore[reportPrivateUsage, arg-type]

    # Case 8: Payload is an empty list (should still be a list of valid items, so returns as is)
    empty_list_payload: list[TextContent | ImageContent | EmbeddedResource] = []
    assert adapter._normalize_payload_to_content_list(empty_list_payload) == empty_list_payload  # type: ignore[reportPrivateUsage]

    # Case 9: Payload is None (should be stringified)
    none_payload = None
    expected_from_none = [TextContent(text=str(none_payload), type="text")]
    assert adapter._normalize_payload_to_content_list(none_payload) == expected_from_none
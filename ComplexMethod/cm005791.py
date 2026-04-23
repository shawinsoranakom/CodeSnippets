async def test_aupdate_message_with_content_blocks(created_message):
    # Create a content block using proper models
    text_content = TextContent(
        type="text", text="Test content", duration=5, header={"title": "Test Header", "icon": "TestIcon"}
    )

    tool_content = ToolContent(type="tool_use", name="test_tool", tool_input={"param": "value"}, duration=10)

    content_block = ContentBlock(title="Test Block", contents=[text_content, tool_content], allow_markdown=True)

    created_message.content_blocks = [content_block]
    created_message.text = "Message with content blocks"

    updated = await aupdate_messages(created_message)

    assert len(updated) == 1
    assert updated[0].text == "Message with content blocks"
    assert len(updated[0].content_blocks) == 1

    # Verify the content block structure
    updated_block = updated[0].content_blocks[0]
    assert updated_block.title == "Test Block"
    expected_len = 2
    assert len(updated_block.contents) == expected_len

    # Verify text content
    text_content = updated_block.contents[0]
    assert text_content.type == "text"
    assert text_content.text == "Test content"
    duration = 5
    assert text_content.duration == duration
    assert text_content.header["title"] == "Test Header"

    # Verify tool content
    tool_content = updated_block.contents[1]
    assert tool_content.type == "tool_use"
    assert tool_content.name == "test_tool"
    assert tool_content.tool_input == {"param": "value"}
    duration = 10
    assert tool_content.duration == duration
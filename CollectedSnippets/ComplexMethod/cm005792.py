async def test_aupdate_message_with_nested_properties(created_message):
    # Create a text content with nested properties
    text_content = TextContent(
        type="text", text="Test content", header={"title": "Test Header", "icon": "TestIcon"}, duration=15
    )

    content_block = ContentBlock(
        title="Test Properties",
        contents=[text_content],
        allow_markdown=True,
        media_url=["http://example.com/image.jpg"],
    )

    # Set properties according to the Properties model structure
    created_message.properties = Properties(
        text_color="blue",
        background_color="white",
        edited=False,
        source=Source(id="test_id", display_name="Test Source", source="test"),
        icon="TestIcon",
        allow_markdown=True,
        state="complete",
        targets=[],
    )
    created_message.text = "Message with nested properties"
    created_message.content_blocks = [content_block]

    updated = await aupdate_messages(created_message)

    assert len(updated) == 1
    assert updated[0].text == "Message with nested properties"

    # Verify the properties were properly serialized and stored
    assert updated[0].properties.text_color == "blue"
    assert updated[0].properties.background_color == "white"
    assert updated[0].properties.edited is False
    assert updated[0].properties.source.id == "test_id"
    assert updated[0].properties.source.display_name == "Test Source"
    assert updated[0].properties.source.source == "test"
    assert updated[0].properties.icon == "TestIcon"
    assert updated[0].properties.allow_markdown is True
    assert updated[0].properties.state == "complete"
    assert updated[0].properties.targets == []
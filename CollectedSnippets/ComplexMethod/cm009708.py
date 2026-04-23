def test_content_block_transformation_v0_to_v1_image() -> None:
    """Test that v0 format image content blocks are transformed to v1 format."""
    # Create a message with v0 format image content
    image_message = AIMessage(
        content=[
            {
                "type": "image",
                "source_type": "url",
                "url": "https://example.com/image.png",
            }
        ]
    )

    llm = GenericFakeChatModel(messages=iter([image_message]), output_version="v1")
    response = llm.invoke("test")

    # With v1 output_version, .content should be transformed
    # Check structure, ignoring auto-generated IDs
    assert len(response.content) == 1
    content_block = response.content[0]
    if isinstance(content_block, dict) and "id" in content_block:
        # Remove auto-generated id for comparison
        content_without_id = {k: v for k, v in content_block.items() if k != "id"}
        expected_content = {
            "type": "image",
            "url": "https://example.com/image.png",
        }
        assert content_without_id == expected_content
    else:
        assert content_block == {
            "type": "image",
            "url": "https://example.com/image.png",
        }
async def test_parse_chat_messages_multiple_image_embeds_async(
    phi3v_model_config_image_embeds,
):
    """Test multiple image_embeds with async parsing.

    This validates the AsyncMultiModalItemTracker also supports multiple embeddings.
    """
    # Create two sample image embedding tensors
    hidden_size = phi3v_model_config_image_embeds.get_inputs_embeds_size()
    image_embedding_1 = torch.randn(200, hidden_size)
    image_embedding_2 = torch.randn(150, hidden_size)

    # Encode them as base64 using the convenience function
    base64_image_embedding_1 = tensor2base64(image_embedding_1)
    base64_image_embedding_2 = tensor2base64(image_embedding_2)

    conversation, mm_data, mm_uuids = await parse_chat_messages_async(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_embeds",
                        "image_embeds": base64_image_embedding_1,
                    },
                    {
                        "type": "image_embeds",
                        "image_embeds": base64_image_embedding_2,
                    },
                    {"type": "text", "text": "What do these images show?"},
                ],
            }
        ],
        phi3v_model_config_image_embeds,
        content_format="string",
    )

    # Verify conversation structure
    assert conversation == [
        {
            "role": "user",
            "content": "<|image_1|>\n<|image_2|>\nWhat do these images show?",
        }
    ]

    # Await the future and verify mm_data
    assert mm_data is not None
    assert "image" in mm_data
    assert isinstance(mm_data["image"], list)
    assert len(mm_data["image"]) == 2

    # Verify each embedding has the correct shape
    assert isinstance(mm_data["image"][0], torch.Tensor)
    assert mm_data["image"][0].shape == image_embedding_1.shape
    assert isinstance(mm_data["image"][1], torch.Tensor)
    assert mm_data["image"][1].shape == image_embedding_2.shape

    # Verify UUIDs
    _assert_mm_uuids(mm_uuids, 2, expected_uuids=[None, None])
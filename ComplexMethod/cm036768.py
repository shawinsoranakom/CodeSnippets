def test_parse_chat_messages_multiple_image_embeds(
    phi3v_model_config_image_embeds,
):
    """Test that multiple image_embeds in a single message are now supported.

    This test validates the fix for the limitation that previously only allowed
    one message with {'type': 'image_embeds'}. Now multiple image embeddings
    can be provided in a single request, similar to regular images.
    """
    # Create two sample image embedding tensors
    hidden_size = phi3v_model_config_image_embeds.get_inputs_embeds_size()
    image_embedding_1 = torch.randn(256, hidden_size)
    image_embedding_2 = torch.randn(128, hidden_size)

    # Encode them as base64 using the convenience function
    base64_image_embedding_1 = tensor2base64(image_embedding_1)
    base64_image_embedding_2 = tensor2base64(image_embedding_2)

    conversation, mm_data, mm_uuids = parse_chat_messages(
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
                    {"type": "text", "text": "Describe these two images."},
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
            "content": "<|image_1|>\n<|image_2|>\nDescribe these two images.",
        }
    ]

    # Verify mm_data contains a list of embeddings (not a single embedding)
    assert mm_data is not None
    assert "image" in mm_data
    assert isinstance(mm_data["image"], list)
    assert len(mm_data["image"]) == 2

    # Verify each embedding has the correct shape
    assert isinstance(mm_data["image"][0], torch.Tensor)
    assert mm_data["image"][0].shape == image_embedding_1.shape
    assert isinstance(mm_data["image"][1], torch.Tensor)
    assert mm_data["image"][1].shape == image_embedding_2.shape

    # Verify UUIDs (None since we didn't provide any)
    _assert_mm_uuids(mm_uuids, 2, expected_uuids=[None, None])
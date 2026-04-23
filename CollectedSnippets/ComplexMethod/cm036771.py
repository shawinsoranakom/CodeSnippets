def test_parse_chat_messages_multiple_dict_image_embeds(
    qwen25omni_model_config_image_embeds,
):
    """Test that multiple dictionaries for image_embeds is handled without errors."""
    # Create two sample image embedding tensors
    batch_size = 2
    hidden_size = qwen25omni_model_config_image_embeds.get_inputs_embeds_size()
    image_embeds = torch.randn(batch_size * 220, hidden_size)
    image_grid_thw = torch.tensor([[1, 22, 40] for _ in range(batch_size)])

    conversation, mm_data, mm_uuids = parse_chat_messages(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_embeds",
                        "image_embeds": {
                            "image_embeds": tensor2base64(embeds),
                            "image_grid_thw": tensor2base64(grid_thw),
                        },
                    }
                    for embeds, grid_thw in zip(
                        image_embeds.chunk(batch_size), image_grid_thw
                    )
                ]
                + [
                    {"type": "text", "text": "Describe these two images."},
                ],
            }
        ],
        qwen25omni_model_config_image_embeds,
        content_format="string",
    )

    # Verify conversation structure
    assert conversation == [
        {
            "role": "user",
            "content": "<|vision_start|><|IMAGE|><|vision_end|>\n"
            "<|vision_start|><|IMAGE|><|vision_end|>\nDescribe these two images.",
        }
    ]

    # Verify mm_data contains a dictionary of multi-embeddings
    assert mm_data is not None
    assert "image" in mm_data
    assert isinstance(mm_data["image"], dict)
    assert len(mm_data["image"]) == batch_size

    # Verify each embedding has the correct shape
    assert isinstance(mm_data["image"]["image_embeds"], torch.Tensor)
    assert mm_data["image"]["image_embeds"].shape == image_embeds.shape
    assert isinstance(mm_data["image"]["image_grid_thw"], torch.Tensor)
    assert mm_data["image"]["image_grid_thw"].shape == image_grid_thw.shape

    # Verify UUIDs (None since we didn't provide any)
    _assert_mm_uuids(mm_uuids, batch_size, expected_uuids=[None, None])
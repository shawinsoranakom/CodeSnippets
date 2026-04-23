def test_parse_chat_messages_multiple_image_embeds_with_uuids(
    phi3v_model_config_image_embeds,
):
    """Test multiple image_embeds with UUIDs.

    This validates that UUIDs are properly tracked for multiple embeddings.
    """
    uuid1 = "image-uuid-1"
    uuid2 = "image-uuid-2"

    conversation, mm_data, mm_uuids = parse_chat_messages(
        [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_embeds",
                        "image_embeds": None,
                        "uuid": uuid1,
                    },
                    {
                        "type": "image_embeds",
                        "image_embeds": None,
                        "uuid": uuid2,
                    },
                    {"type": "text", "text": "Compare these images."},
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
            "content": "<|image_1|>\n<|image_2|>\nCompare these images.",
        }
    ]

    # Verify mm_data contains a list with None values (UUID references)
    assert mm_data is not None
    assert "image" in mm_data
    assert isinstance(mm_data["image"], list)
    assert len(mm_data["image"]) == 2
    assert mm_data["image"][0] is None
    assert mm_data["image"][1] is None

    # Verify UUIDs are correctly tracked
    _assert_mm_uuids(mm_uuids, 2, expected_uuids=[uuid1, uuid2])
async def test_block_handler_get_missing_items():
    """Test BlockHandler discovers blocks without embeddings."""
    handler = BlockHandler()

    blocks = {
        "block-uuid-1": _make_block_class(
            name="CalculatorBlock",
            description="Performs calculations",
            categories=[MagicMock(value="MATH")],
            fields={"expression": "Math expression to evaluate"},
        ),
    }

    with patch(
        "backend.api.features.store.content_handlers.get_blocks", return_value=blocks
    ):
        with patch(
            "backend.api.features.store.content_handlers.query_raw_with_schema",
            return_value=[],
        ):
            items = await handler.get_missing_items(batch_size=10)

            assert len(items) == 1
            assert items[0].content_id == "block-uuid-1"
            assert items[0].content_type == ContentType.BLOCK
            # CamelCase should be split in searchable text and metadata name
            assert "Calculator Block" in items[0].searchable_text
            assert "Performs calculations" in items[0].searchable_text
            assert "MATH" in items[0].searchable_text
            assert "expression: Math expression" in items[0].searchable_text
            assert items[0].metadata["name"] == "Calculator Block"
            assert items[0].user_id is None
async def test_documentation_handler_get_missing_items(tmp_path, mocker):
    """Test DocumentationHandler discovers docs without embeddings."""
    handler = DocumentationHandler()

    docs_root = tmp_path / "docs"
    docs_root.mkdir()
    (docs_root / "guide.md").write_text("# Getting Started\n\nThis is a guide.")
    (docs_root / "api.mdx").write_text("# API Reference\n\nAPI documentation.")

    with patch.object(handler, "_get_docs_root", return_value=docs_root):
        with patch(
            "backend.api.features.store.content_handlers.query_raw_with_schema",
            return_value=[],
        ):
            items = await handler.get_missing_items(batch_size=10)

            assert len(items) == 2

            guide_item = next(
                (item for item in items if item.content_id == "guide.md::0"), None
            )
            assert guide_item is not None
            assert guide_item.content_type == ContentType.DOCUMENTATION
            assert "Getting Started" in guide_item.searchable_text
            assert "This is a guide" in guide_item.searchable_text
            assert guide_item.metadata["doc_title"] == "Getting Started"
            assert guide_item.user_id is None

            api_item = next(
                (item for item in items if item.content_id == "api.mdx::0"), None
            )
            assert api_item is not None
            assert "API Reference" in api_item.searchable_text
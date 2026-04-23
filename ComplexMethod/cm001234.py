async def test_documentation_handler_markdown_chunking(tmp_path):
    """Test DocumentationHandler chunks markdown by headings."""
    handler = DocumentationHandler()

    doc_with_sections = tmp_path / "sections.md"
    doc_with_sections.write_text(
        "# Document Title\n\n"
        "Intro paragraph.\n\n"
        "## Section One\n\n"
        "Content for section one.\n\n"
        "## Section Two\n\n"
        "Content for section two.\n"
    )
    sections = handler._chunk_markdown_by_headings(doc_with_sections)

    assert len(sections) == 3
    assert sections[0].title == "Document Title"
    assert sections[0].index == 0
    assert "Intro paragraph" in sections[0].content

    assert sections[1].title == "Section One"
    assert sections[1].index == 1
    assert "Content for section one" in sections[1].content

    assert sections[2].title == "Section Two"
    assert sections[2].index == 2
    assert "Content for section two" in sections[2].content

    doc_no_sections = tmp_path / "no-sections.md"
    doc_no_sections.write_text("Just plain content without any headings.")
    sections = handler._chunk_markdown_by_headings(doc_no_sections)
    assert len(sections) == 1
    assert sections[0].index == 0
    assert "Just plain content" in sections[0].content
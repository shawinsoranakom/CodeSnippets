def test_create_chunks_with_empty_lines():
    text = 'line1\n\nline3\n\n\nline6'
    chunks = create_chunks(text, size=2)
    assert len(chunks) == 3
    assert chunks[0].text == 'line1\n'
    assert chunks[0].line_range == (1, 2)
    assert chunks[1].text == 'line3\n'
    assert chunks[1].line_range == (3, 4)
    assert chunks[2].text == '\nline6'
    assert chunks[2].line_range == (5, 6)
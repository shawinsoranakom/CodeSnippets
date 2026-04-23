def test_create_chunks_raw_string():
    text = 'line1\nline2\nline3\nline4\nline5'
    chunks = create_chunks(text, size=2)
    assert len(chunks) == 3
    assert chunks[0].text == 'line1\nline2'
    assert chunks[0].line_range == (1, 2)
    assert chunks[1].text == 'line3\nline4'
    assert chunks[1].line_range == (3, 4)
    assert chunks[2].text == 'line5'
    assert chunks[2].line_range == (5, 5)
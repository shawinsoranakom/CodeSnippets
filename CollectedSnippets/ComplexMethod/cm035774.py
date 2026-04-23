def test_get_top_k_chunk_matches():
    text = 'chunk1\nchunk2\nchunk3\nchunk4'
    query = 'chunk2'
    matches = get_top_k_chunk_matches(text, query, k=2, max_chunk_size=1)
    assert len(matches) == 2
    assert matches[0].text == 'chunk2'
    assert matches[0].line_range == (2, 2)
    assert matches[0].normalized_lcs == 1.0
    assert matches[1].text == 'chunk1'
    assert matches[1].line_range == (1, 1)
    assert matches[1].normalized_lcs == 5 / 6
    assert matches[0].normalized_lcs > matches[1].normalized_lcs
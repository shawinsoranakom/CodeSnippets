def _test_online_1_v_n(server):
    # test scoring api
    scores = _get_scores(server, query, documents)
    assert len(scores) == len(documents)

    for expected, actual in zip(REFERENCE_1_VS_N, scores):
        assert actual == pytest.approx(expected, abs=TOL)

    # test pooling api
    embeds = _get_embeds(server, documents + [query])
    assert embeds.shape[0] == len(documents) + 1

    doc_embeds = embeds[:-1]
    query_embeds = embeds[-1]

    scores = F.cosine_similarity(query_embeds, doc_embeds)

    assert len(scores) == len(documents)
    for expected, actual in zip(REFERENCE_1_VS_N, scores):
        assert actual == pytest.approx(expected, abs=TOL)
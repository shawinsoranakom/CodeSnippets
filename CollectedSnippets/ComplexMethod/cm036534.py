def _test_online_n_v_n(server):
    # test scoring api
    scores = _get_scores(server, [query] * len(documents), documents)
    assert len(scores) == len(documents)

    for expected, actual in zip(REFERENCE_1_VS_1, scores):
        assert actual == pytest.approx(expected, abs=TOL)

    # test pooling api
    for doc, expected in zip(documents, REFERENCE_1_VS_1):
        embeds = _get_embeds(server, [doc, query])
        assert embeds.shape[0] == 2

        doc_embeds = embeds[:-1]
        query_embeds = embeds[-1]

        scores = F.cosine_similarity(query_embeds, doc_embeds)
        assert len(scores) == 1
        assert scores[0] == pytest.approx(expected, abs=TOL)
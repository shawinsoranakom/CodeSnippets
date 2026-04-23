def test_visual_predict(pp_chatocrv4_doc_pipeline, image_path):
    result = pp_chatocrv4_doc_pipeline.visual_predict(str(image_path))

    assert result is not None
    assert isinstance(result, list)
    assert len(result) == 1
    res = result[0]
    assert isinstance(res, dict)
    assert res.keys() == {"visual_info", "layout_parsing_result"}
    assert isinstance(res["visual_info"], dict)
    assert isinstance(res["layout_parsing_result"], dict)
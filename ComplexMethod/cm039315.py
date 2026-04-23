def test_pipeline_ducktyping():
    pipeline = make_pipeline(Mult(5))
    pipeline.predict
    pipeline.transform
    pipeline.inverse_transform

    pipeline = make_pipeline(Transf())
    assert not hasattr(pipeline, "predict")
    pipeline.transform
    pipeline.inverse_transform

    pipeline = make_pipeline("passthrough")
    assert pipeline.steps[0] == ("passthrough", "passthrough")
    assert not hasattr(pipeline, "predict")
    pipeline.transform
    pipeline.inverse_transform

    pipeline = make_pipeline(Transf(), NoInvTransf())
    assert not hasattr(pipeline, "predict")
    pipeline.transform
    assert not hasattr(pipeline, "inverse_transform")

    pipeline = make_pipeline(NoInvTransf(), Transf())
    assert not hasattr(pipeline, "predict")
    pipeline.transform
    assert not hasattr(pipeline, "inverse_transform")
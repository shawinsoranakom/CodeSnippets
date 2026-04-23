def test_make_pipeline():
    t1 = Transf()
    t2 = Transf()
    pipe = make_pipeline(t1, t2)
    assert isinstance(pipe, Pipeline)
    assert pipe.steps[0][0] == "transf-1"
    assert pipe.steps[1][0] == "transf-2"

    pipe = make_pipeline(t1, t2, FitParamT())
    assert isinstance(pipe, Pipeline)
    assert pipe.steps[0][0] == "transf-1"
    assert pipe.steps[1][0] == "transf-2"
    assert pipe.steps[2][0] == "fitparamt"
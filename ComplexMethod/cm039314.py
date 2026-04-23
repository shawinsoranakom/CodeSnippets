def test_pipeline_invalid_parameters():
    # Test the various init parameters of the pipeline in fit
    # method
    pipeline = Pipeline([(1, 1)])
    with pytest.raises(TypeError):
        pipeline.fit([[1]], [1])

    # Check that we can't fit pipelines with objects without fit
    # method
    msg = (
        "Last step of Pipeline should implement fit "
        "or be the string 'passthrough'"
        ".*NoFit.*"
    )
    pipeline = Pipeline([("clf", NoFit())])
    with pytest.raises(TypeError, match=msg):
        pipeline.fit([[1]], [1])

    # Smoke test with only an estimator
    clf = NoTrans()
    pipe = Pipeline([("svc", clf)])
    assert pipe.get_params(deep=True) == dict(
        svc__a=None, svc__b=None, svc=clf, **pipe.get_params(deep=False)
    )

    # Check that params are set
    pipe.set_params(svc__a=0.1)
    assert clf.a == 0.1
    assert clf.b is None
    # Smoke test the repr:
    repr(pipe)

    # Test with two objects
    clf = SVC()
    filter1 = SelectKBest(f_classif)
    pipe = Pipeline([("anova", filter1), ("svc", clf)])

    # Check that estimators are not cloned on pipeline construction
    assert pipe.named_steps["anova"] is filter1
    assert pipe.named_steps["svc"] is clf

    # Check that we can't fit with non-transformers on the way
    # Note that NoTrans implements fit, but not transform
    msg = "All intermediate steps should be transformers.*\\bNoTrans\\b.*"
    pipeline = Pipeline([("t", NoTrans()), ("svc", clf)])
    with pytest.raises(TypeError, match=msg):
        pipeline.fit([[1]], [1])

    # Check that params are set
    pipe.set_params(svc__C=0.1)
    assert clf.C == 0.1
    # Smoke test the repr:
    repr(pipe)

    # Check that params are not set when naming them wrong
    msg = re.escape(
        "Invalid parameter 'C' for estimator SelectKBest(). Valid parameters are: ['k',"
        " 'score_func']."
    )
    with pytest.raises(ValueError, match=msg):
        pipe.set_params(anova__C=0.1)

    # Test clone
    pipe2 = clone(pipe)
    assert pipe.named_steps["svc"] is not pipe2.named_steps["svc"]

    # Check that apart from estimators, the parameters are the same
    params = pipe.get_params(deep=True)
    params2 = pipe2.get_params(deep=True)

    for x in pipe.get_params(deep=False):
        params.pop(x)

    for x in pipe2.get_params(deep=False):
        params2.pop(x)

    # Remove estimators that where copied
    params.pop("svc")
    params.pop("anova")
    params2.pop("svc")
    params2.pop("anova")
    assert params == params2
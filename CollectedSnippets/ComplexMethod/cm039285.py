def test_feature_names():
    cv = CountVectorizer(max_df=0.5)

    # test for Value error on unfitted/empty vocabulary
    with pytest.raises(ValueError):
        cv.get_feature_names_out()
    assert not cv.fixed_vocabulary_

    # test for vocabulary learned from data
    X = cv.fit_transform(ALL_FOOD_DOCS)
    n_samples, n_features = X.shape
    assert len(cv.vocabulary_) == n_features

    feature_names = cv.get_feature_names_out()
    assert isinstance(feature_names, np.ndarray)
    assert feature_names.dtype == object

    assert len(feature_names) == n_features
    assert_array_equal(
        [
            "beer",
            "burger",
            "celeri",
            "coke",
            "pizza",
            "salad",
            "sparkling",
            "tomato",
            "water",
        ],
        feature_names,
    )

    for idx, name in enumerate(feature_names):
        assert idx == cv.vocabulary_.get(name)

    # test for custom vocabulary
    vocab = [
        "beer",
        "burger",
        "celeri",
        "coke",
        "pizza",
        "salad",
        "sparkling",
        "tomato",
        "water",
    ]

    cv = CountVectorizer(vocabulary=vocab)
    feature_names = cv.get_feature_names_out()
    assert_array_equal(
        [
            "beer",
            "burger",
            "celeri",
            "coke",
            "pizza",
            "salad",
            "sparkling",
            "tomato",
            "water",
        ],
        feature_names,
    )
    assert cv.fixed_vocabulary_

    for idx, name in enumerate(feature_names):
        assert idx == cv.vocabulary_.get(name)
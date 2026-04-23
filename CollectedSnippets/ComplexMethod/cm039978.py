def test_estimator_html_repr_pipeline():
    num_trans = Pipeline(
        steps=[("pass", "passthrough"), ("imputer", SimpleImputer(strategy="median"))]
    )

    cat_trans = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", missing_values="empty")),
            ("one-hot", OneHotEncoder(drop="first")),
        ]
    )

    preprocess = ColumnTransformer(
        [
            ("num", num_trans, ["a", "b", "c", "d", "e"]),
            ("cat", cat_trans, [0, 1, 2, 3]),
        ]
    )

    feat_u = FeatureUnion(
        [
            ("pca", PCA(n_components=1)),
            (
                "tsvd",
                Pipeline(
                    [
                        ("first", TruncatedSVD(n_components=3)),
                        ("select", SelectPercentile()),
                    ]
                ),
            ),
        ]
    )

    clf = VotingClassifier(
        [
            ("lr", LogisticRegression(solver="lbfgs", random_state=1)),
            ("mlp", MLPClassifier(alpha=0.001)),
        ]
    )

    pipe = Pipeline(
        [("preprocessor", preprocess), ("feat_u", feat_u), ("classifier", clf)]
    )
    html_output = estimator_html_repr(pipe)

    # top level estimators show estimator with changes
    assert html.escape(str(pipe)) in html_output
    for _, est in pipe.steps:
        assert html.escape(str(est))[:44] in html_output

    # low level estimators do not show changes
    with config_context(print_changed_only=True):
        assert html.escape(str(num_trans["pass"])) in html_output
        assert "<div><div>passthrough</div></div></label>" in html_output
        assert html.escape(str(num_trans["imputer"])) in html_output

        for _, _, cols in preprocess.transformers:
            assert f"<pre>{html.escape(str(cols))}</pre>" in html_output

        # feature union
        for name, _ in feat_u.transformer_list:
            assert f"<label>{html.escape(name)}</label>" in html_output

        pca = feat_u.transformer_list[0][1]

        assert html.escape(str(pca)) in html_output

        tsvd = feat_u.transformer_list[1][1]
        first = tsvd["first"]
        select = tsvd["select"]
        assert html.escape(str(first)) in html_output
        assert html.escape(str(select)) in html_output

        # voting classifier
        for name, est in clf.estimators:
            assert html.escape(name) in html_output
            assert html.escape(str(est)) in html_output

    # verify that prefers-color-scheme is implemented
    assert "prefers-color-scheme" in html_output
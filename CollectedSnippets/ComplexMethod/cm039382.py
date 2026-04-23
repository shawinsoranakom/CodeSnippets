def test_precision():
    rng_reg = RandomState(2)
    rng_clf = RandomState(8)
    for X, y, clf in zip(
        (rng_reg.random_sample((5, 2)), rng_clf.random_sample((1000, 4))),
        (rng_reg.random_sample((5,)), rng_clf.randint(2, size=(1000,))),
        (
            DecisionTreeRegressor(random_state=0, max_depth=1),
            DecisionTreeClassifier(max_depth=1, random_state=0),
        ),
    ):
        clf.fit(X, y)
        for precision in (4, 3):
            dot_data = export_graphviz(
                clf, out_file=None, precision=precision, proportion=True
            )

            # With the current random state, the impurity and the threshold
            # will have the number of precision set in the export_graphviz
            # function. We will check the number of precision with a strict
            # equality. The value reported will have only 2 precision and
            # therefore, only a less equal comparison will be done.

            # check value
            for finding in finditer(r"value = \d+\.\d+", dot_data):
                assert len(search(r"\.\d+", finding.group()).group()) <= precision + 1
            # check impurity
            if is_classifier(clf):
                pattern = r"gini = \d+\.\d+"
            else:
                pattern = r"squared_error = \d+\.\d+"

            # check impurity
            for finding in finditer(pattern, dot_data):
                assert len(search(r"\.\d+", finding.group()).group()) == precision + 1
            # check threshold
            for finding in finditer(r"<= \d+\.\d+", dot_data):
                assert len(search(r"\.\d+", finding.group()).group()) == precision + 1
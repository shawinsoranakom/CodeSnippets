def test_export_text():
    clf = DecisionTreeClassifier(max_depth=2, random_state=0)
    clf.fit(X, y)

    expected_report = dedent(
        """
    |--- feature_1 <= 0.00
    |   |--- class: -1
    |--- feature_1 >  0.00
    |   |--- class: 1
    """
    ).lstrip()

    assert export_text(clf) == expected_report
    # testing that leaves at level 1 are not truncated
    assert export_text(clf, max_depth=0) == expected_report
    # testing that the rest of the tree is truncated
    assert export_text(clf, max_depth=10) == expected_report

    expected_report = dedent(
        """
    |--- feature_1 <= 0.00
    |   |--- weights: [3.00, 0.00] class: -1
    |--- feature_1 >  0.00
    |   |--- weights: [0.00, 3.00] class: 1
    """
    ).lstrip()
    assert export_text(clf, show_weights=True) == expected_report

    expected_report = dedent(
        """
    |- feature_1 <= 0.00
    | |- class: -1
    |- feature_1 >  0.00
    | |- class: 1
    """
    ).lstrip()
    assert export_text(clf, spacing=1) == expected_report

    X_l = [[-2, -1], [-1, -1], [-1, -2], [1, 1], [1, 2], [2, 1], [-1, 1]]
    y_l = [-1, -1, -1, 1, 1, 1, 2]
    clf = DecisionTreeClassifier(max_depth=4, random_state=0)
    clf.fit(X_l, y_l)
    expected_report = dedent(
        """
    |--- feature_1 <= 0.00
    |   |--- class: -1
    |--- feature_1 >  0.00
    |   |--- truncated branch of depth 2
    """
    ).lstrip()
    assert export_text(clf, max_depth=0) == expected_report

    X_mo = [[-2, -1], [-1, -1], [-1, -2], [1, 1], [1, 2], [2, 1]]
    y_mo = [[-1, -1], [-1, -1], [-1, -1], [1, 1], [1, 1], [1, 1]]

    reg = DecisionTreeRegressor(max_depth=2, random_state=0)
    reg.fit(X_mo, y_mo)

    expected_report = dedent(
        """
    |--- feature_1 <= 0.0
    |   |--- value: [-1.0, -1.0]
    |--- feature_1 >  0.0
    |   |--- value: [1.0, 1.0]
    """
    ).lstrip()
    assert export_text(reg, decimals=1) == expected_report
    assert export_text(reg, decimals=1, show_weights=True) == expected_report

    X_single = [[-2], [-1], [-1], [1], [1], [2]]
    reg = DecisionTreeRegressor(max_depth=2, random_state=0)
    reg.fit(X_single, y_mo)

    expected_report = dedent(
        """
    |--- first <= 0.0
    |   |--- value: [-1.0, -1.0]
    |--- first >  0.0
    |   |--- value: [1.0, 1.0]
    """
    ).lstrip()
    assert export_text(reg, decimals=1, feature_names=["first"]) == expected_report
    assert (
        export_text(reg, decimals=1, show_weights=True, feature_names=["first"])
        == expected_report
    )
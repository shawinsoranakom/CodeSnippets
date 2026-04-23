def test_plot_tree_gini(pyplot, fontsize):
    # mostly smoke tests
    # Check correctness of export_graphviz for criterion = gini
    clf = DecisionTreeClassifier(
        max_depth=3,
        min_samples_split=2,
        criterion="gini",
        random_state=2,
    )
    clf.fit(X, y)

    # Test export code
    feature_names = ["first feat", "sepal_width"]
    nodes = plot_tree(clf, feature_names=feature_names, fontsize=fontsize)
    assert len(nodes) == 5
    if fontsize is not None:
        assert all(node.get_fontsize() == fontsize for node in nodes)
    assert (
        nodes[0].get_text()
        == "first feat <= 0.0\ngini = 0.5\nsamples = 6\nvalue = [3, 3]"
    )
    assert nodes[1].get_text() == "gini = 0.0\nsamples = 3\nvalue = [3, 0]"
    assert nodes[2].get_text() == "True  "
    assert nodes[3].get_text() == "gini = 0.0\nsamples = 3\nvalue = [0, 3]"
    assert nodes[4].get_text() == "  False"
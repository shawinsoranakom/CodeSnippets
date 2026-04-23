def test_summarize():
    # Simple check for quad tree's summarize

    angle = 0.9
    X = np.array(
        [[-10.0, -10.0], [9.0, 10.0], [10.0, 9.0], [10.0, 10.0]], dtype=np.float32
    )
    query_pt = X[0, :]
    n_dimensions = X.shape[1]
    offset = n_dimensions + 2

    qt = _QuadTree(n_dimensions, verbose=0)
    qt.build_tree(X)

    idx, summary = qt._py_summarize(query_pt, X, angle)

    node_dist = summary[n_dimensions]
    node_size = summary[n_dimensions + 1]

    # Summary should contain only 1 node with size 3 and distance to
    # X[1:] barycenter
    barycenter = X[1:].mean(axis=0)
    ds2c = ((X[0] - barycenter) ** 2).sum()

    assert idx == offset
    assert node_size == 3, "summary size = {}".format(node_size)
    assert np.isclose(node_dist, ds2c)

    # Summary should contain all 3 node with size 1 and distance to
    # each point in X[1:] for ``angle=0``
    idx, summary = qt._py_summarize(query_pt, X, 0.0)
    barycenter = X[1:].mean(axis=0)
    ds2c = ((X[0] - barycenter) ** 2).sum()

    assert idx == 3 * (offset)
    for i in range(3):
        node_dist = summary[i * offset + n_dimensions]
        node_size = summary[i * offset + n_dimensions + 1]

        ds2c = ((X[0] - X[i + 1]) ** 2).sum()

        assert node_size == 1, "summary size = {}".format(node_size)
        assert np.isclose(node_dist, ds2c)
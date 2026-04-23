def test_max_features():
    # Check max_features.
    for name, TreeEstimator in ALL_TREES.items():
        est = TreeEstimator(max_features="sqrt")
        est.fit(iris.data, iris.target)
        assert est.max_features_ == int(np.sqrt(iris.data.shape[1]))

        est = TreeEstimator(max_features="log2")
        est.fit(iris.data, iris.target)
        assert est.max_features_ == int(np.log2(iris.data.shape[1]))

        est = TreeEstimator(max_features=1)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == 1

        est = TreeEstimator(max_features=3)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == 3

        est = TreeEstimator(max_features=0.01)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == 1

        est = TreeEstimator(max_features=0.5)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == int(0.5 * iris.data.shape[1])

        est = TreeEstimator(max_features=1.0)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == iris.data.shape[1]

        est = TreeEstimator(max_features=None)
        est.fit(iris.data, iris.target)
        assert est.max_features_ == iris.data.shape[1]
def test_feature_hasher_strings():
    # mix byte and Unicode strings; note that "foo" is a duplicate in row 0
    raw_X = [
        ["foo", "bar", "baz", "foo".encode("ascii")],
        ["bar".encode("ascii"), "baz", "quux"],
    ]

    for lg_n_features in (7, 9, 11, 16, 22):
        n_features = 2**lg_n_features

        it = (x for x in raw_X)  # iterable

        feature_hasher = FeatureHasher(
            n_features=n_features, input_type="string", alternate_sign=False
        )
        X = feature_hasher.transform(it)

        assert X.shape[0] == len(raw_X)
        assert X.shape[1] == n_features

        if SCIPY_VERSION_BELOW_1_12:
            assert X[[0], :].sum() == 4
            assert X[[1], :].sum() == 3
        else:
            assert X[0].sum() == 4
            assert X[1].sum() == 3

        assert X.nnz == 6
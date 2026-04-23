def test_one_hot_encoder_categories(X, cat_exp, cat_dtype):
    # order of categories should not depend on order of samples
    for Xi in [X, X[::-1]]:
        enc = OneHotEncoder(categories="auto")
        enc.fit(Xi)
        # assert enc.categories == 'auto'
        assert isinstance(enc.categories_, list)
        for res, exp in zip(enc.categories_, cat_exp):
            res_list = res.tolist()
            if is_scalar_nan(exp[-1]):
                assert is_scalar_nan(res_list[-1])
                assert res_list[:-1] == exp[:-1]
            else:
                assert res.tolist() == exp
            assert np.issubdtype(res.dtype, cat_dtype)
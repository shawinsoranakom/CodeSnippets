def test_array_api_train_test_split(
    shuffle, stratify, array_namespace, device_name, dtype_name
):
    xp, device = _array_api_for_tests(array_namespace, device_name)

    X = np.arange(100).reshape((10, 10))
    y = np.arange(10)

    X_np = X.astype(dtype_name)
    X_xp = xp.asarray(X_np, device=device)

    y_np = y.astype(dtype_name)
    y_xp = xp.asarray(y_np, device=device)

    X_train_np, X_test_np, y_train_np, y_test_np = train_test_split(
        X_np, y, random_state=0, shuffle=shuffle, stratify=stratify
    )
    with config_context(array_api_dispatch=True):
        if stratify is not None:
            stratify_xp = xp.asarray(stratify)
        else:
            stratify_xp = stratify
        X_train_xp, X_test_xp, y_train_xp, y_test_xp = train_test_split(
            X_xp, y_xp, shuffle=shuffle, stratify=stratify_xp, random_state=0
        )

        # Check that namespace is preserved, has to happen with
        # array_api_dispatch enabled.
        assert get_namespace(X_train_xp)[0] == get_namespace(X_xp)[0]
        assert get_namespace(X_test_xp)[0] == get_namespace(X_xp)[0]
        assert get_namespace(y_train_xp)[0] == get_namespace(y_xp)[0]
        assert get_namespace(y_test_xp)[0] == get_namespace(y_xp)[0]

        # Check device and dtype is preserved on output
        assert array_api_device(X_train_xp) == array_api_device(X_xp)
        assert array_api_device(y_train_xp) == array_api_device(y_xp)
        assert array_api_device(X_test_xp) == array_api_device(X_xp)
        assert array_api_device(y_test_xp) == array_api_device(y_xp)

    assert X_train_xp.dtype == X_xp.dtype
    assert y_train_xp.dtype == y_xp.dtype
    assert X_test_xp.dtype == X_xp.dtype
    assert y_test_xp.dtype == y_xp.dtype

    assert_allclose(
        move_to(X_train_xp, xp=np, device="cpu"),
        X_train_np,
    )
    assert_allclose(
        move_to(X_test_xp, xp=np, device="cpu"),
        X_test_np,
    )
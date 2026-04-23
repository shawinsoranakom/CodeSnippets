def test_label_binarize_array_api_compliance(
    y, classes, expected, array_namespace, device_name, dtype_name
):
    """Test that :func:`label_binarize` works correctly with the Array API for binary
    and multi-class inputs for numerical labels and non-sparse outputs.
    """
    xp, device = _array_api_for_tests(array_namespace, device_name)
    xp_is_numpy = _is_numpy_namespace(xp)
    numeric_dtype = np.issubdtype(np.asarray(y).dtype, np.integer) and np.issubdtype(
        np.asarray(classes).dtype, np.integer
    )

    with config_context(array_api_dispatch=True):
        y = xp.asarray(y, device=device)

        if numeric_dtype:
            # `sparse_output=True` is not allowed for non-NumPy namespaces
            if not xp_is_numpy:
                msg = "`sparse_output=True` is not supported for array API "
                with pytest.raises(ValueError, match=msg):
                    label_binarize(y=y, classes=classes, sparse_output=True)

            # Numeric class labels should not raise any errors for non-NumPy namespaces
            binarized = label_binarize(y, classes=classes)
            expected = np.asarray(expected, dtype=int)

            assert get_namespace(binarized)[0].__name__ == xp.__name__
            assert array_api_device(binarized) == array_api_device(y)
            assert "int" in str(binarized.dtype)
            assert_array_equal(move_to(binarized, xp=np, device="cpu"), expected)

        if not xp_is_numpy and not numeric_dtype:
            msg = "`classes` contains unsupported dtype for array API "
            with pytest.raises(ValueError, match=msg):
                label_binarize(y=y, classes=classes)
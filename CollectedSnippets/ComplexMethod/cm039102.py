def test_label_binarizer_array_api_compliance(
    y, classes, expected, array_namespace, device_name, dtype_name
):
    """Test that :class:`LabelBinarizer` works correctly with the Array API for binary
    and multi-class inputs for numerical labels and non-sparse outputs.
    """
    xp, device = _array_api_for_tests(array_namespace, device_name)

    y_np = np.asarray(y)

    with config_context(array_api_dispatch=True):
        y = xp.asarray(y, device=device)

        # `sparse_output=True` is not allowed for non-NumPy namespaces.
        # Similarly, if `LabelBinarizer` is fitted on a sparse matrix,
        # then inverse-transforming non-NumPy arrays is not allowed.
        if not _is_numpy_namespace(xp):
            sparse_output_msg = "`sparse_output=True` is not supported for array API"

            with pytest.raises(ValueError, match=sparse_output_msg):
                LabelBinarizer(sparse_output=True).fit(y)

            lb_np = LabelBinarizer(sparse_output=True).fit(y_np)
            with pytest.raises(ValueError, match=sparse_output_msg):
                lb_np.transform(y)

            lb_sparse = LabelBinarizer().fit(y_np)
            lb_sparse.sparse_input_ = True
            sparse_input_msg = (
                "`LabelBinarizer` was fitted on a sparse matrix, and therefore cannot"
            )
            with pytest.raises(ValueError, match=sparse_input_msg):
                lb_sparse.inverse_transform(xp.asarray(expected, device=device))

        # Shouldn't raise error in both `fit` and `transform` when `sparse_output=False`
        lb_xp = LabelBinarizer()

        binarized = lb_xp.fit_transform(y)
        assert get_namespace(binarized)[0].__name__ == xp.__name__
        assert "int" in str(binarized.dtype)
        assert array_api_device(binarized) == array_api_device(y)
        assert_array_equal(
            move_to(binarized, xp=np, device="cpu"), np.asarray(expected)
        )

        fitted_classes = lb_xp.classes_
        assert get_namespace(fitted_classes)[0].__name__ == xp.__name__
        assert array_api_device(fitted_classes) == array_api_device(y)
        assert "int" in str(fitted_classes.dtype)
        assert_array_equal(
            move_to(fitted_classes, xp=np, device="cpu"), np.asarray(classes)
        )

        expected_xp = xp.asarray(expected, device=device)
        binarized_inverse = lb_xp.inverse_transform(expected_xp)
        assert get_namespace(binarized_inverse)[0].__name__ == xp.__name__
        assert "int" in str(binarized_inverse.dtype)
        assert array_api_device(binarized_inverse) == array_api_device(y)
        assert_array_equal(
            move_to(binarized_inverse, xp=np, device="cpu"),
            move_to(y, xp=np, device="cpu"),
        )
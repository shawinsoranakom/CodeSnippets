def check_binarized_results(y, classes, pos_label, neg_label, expected):
    for sparse_output in [True, False]:
        if (pos_label == 0 or neg_label != 0) and sparse_output:
            with pytest.raises(ValueError):
                label_binarize(
                    y,
                    classes=classes,
                    neg_label=neg_label,
                    pos_label=pos_label,
                    sparse_output=sparse_output,
                )
            continue

        # check label_binarize
        binarized = label_binarize(
            y,
            classes=classes,
            neg_label=neg_label,
            pos_label=pos_label,
            sparse_output=sparse_output,
        )
        assert_array_equal(toarray(binarized), expected)
        assert issparse(binarized) == sparse_output

        # check inverse
        y_type = type_of_target(y)
        if y_type == "multiclass":
            inversed = _inverse_binarize_multiclass(binarized, classes=classes)

        else:
            inversed = _inverse_binarize_thresholding(
                binarized,
                output_type=y_type,
                classes=classes,
                threshold=((neg_label + pos_label) / 2.0),
            )

        assert_array_equal(toarray(inversed), toarray(y))

        # Check label binarizer
        lb = LabelBinarizer(
            neg_label=neg_label, pos_label=pos_label, sparse_output=sparse_output
        )
        binarized = lb.fit_transform(y)
        assert_array_equal(toarray(binarized), expected)
        assert issparse(binarized) == sparse_output
        inverse_output = lb.inverse_transform(binarized)
        assert_array_equal(toarray(inverse_output), toarray(y))
        assert issparse(inverse_output) == issparse(y)
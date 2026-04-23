def _output_from_fit_transform(transformer, name, X, df, y):
    """Generate output to test `set_output` for different configuration:

    - calling either `fit.transform` or `fit_transform`;
    - passing either a dataframe or a numpy array to fit;
    - passing either a dataframe or a numpy array to transform.
    """
    outputs = {}

    # fit then transform case:
    cases = [
        ("fit.transform/df/df", df, df),
        ("fit.transform/df/array", df, X),
        ("fit.transform/array/df", X, df),
        ("fit.transform/array/array", X, X),
    ]
    if all(hasattr(transformer, meth) for meth in ["fit", "transform"]):
        for (
            case,
            data_fit,
            data_transform,
        ) in cases:
            transformer.fit(data_fit, y)
            if name in CROSS_DECOMPOSITION:
                X_trans, _ = transformer.transform(data_transform, y)
            else:
                X_trans = transformer.transform(data_transform)
            outputs[case] = (X_trans, transformer.get_feature_names_out())

    # fit_transform case:
    cases = [
        ("fit_transform/df", df),
        ("fit_transform/array", X),
    ]
    if hasattr(transformer, "fit_transform"):
        for case, data in cases:
            if name in CROSS_DECOMPOSITION:
                X_trans, _ = transformer.fit_transform(data, y)
            else:
                X_trans = transformer.fit_transform(data, y)
            outputs[case] = (X_trans, transformer.get_feature_names_out())

    return outputs
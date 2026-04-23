def _check_set_output_transform_dataframe(
    name,
    transformer_orig,
    *,
    dataframe_lib,
    is_supported_dataframe,
    create_dataframe,
    assert_frame_equal,
    context,
):
    """Check that a transformer can output a DataFrame when requested.

    The DataFrame implementation is specified through the parameters of this function.

    Parameters
    ----------
    name : str
        The name of the transformer.
    transformer_orig : estimator
        The original transformer instance.
    dataframe_lib : str
        The name of the library implementing the DataFrame.
    is_supported_dataframe : callable
        A callable that takes a DataFrame instance as input and returns whether or
        not it is supported by the dataframe library.
        E.g. `lambda X: isintance(X, pd.DataFrame)`.
    create_dataframe : callable
        A callable taking as parameters `data`, `columns`, and `index` and returns
        a callable. Be aware that `index` can be ignored. For example, polars dataframes
        will ignore the index.
    assert_frame_equal : callable
        A callable taking 2 dataframes to compare if they are equal.
    context : {"local", "global"}
        Whether to use a local context by setting `set_output(...)` on the transformer
        or a global context by using the `with config_context(...)`
    """
    # Check transformer.set_output configures the output of transform="pandas".
    tags = get_tags(transformer_orig)
    if not tags.input_tags.two_d_array or tags.no_validation:
        return

    rng = np.random.RandomState(0)
    transformer = clone(transformer_orig)

    X = rng.uniform(size=(20, 5))
    X = _enforce_estimator_tags_X(transformer_orig, X)
    y = rng.randint(0, 2, size=20)
    y = _enforce_estimator_tags_y(transformer_orig, y)
    set_random_state(transformer)

    feature_names_in = [f"col{i}" for i in range(X.shape[1])]
    index = [f"index{i}" for i in range(X.shape[0])]
    df = create_dataframe(X, columns=feature_names_in, index=index)

    transformer_default = clone(transformer).set_output(transform="default")
    outputs_default = _output_from_fit_transform(transformer_default, name, X, df, y)

    if context == "local":
        transformer_df = clone(transformer).set_output(transform=dataframe_lib)
        context_to_use = nullcontext()
    else:  # global
        transformer_df = clone(transformer)
        context_to_use = config_context(transform_output=dataframe_lib)

    try:
        with context_to_use:
            outputs_df = _output_from_fit_transform(transformer_df, name, X, df, y)
    except ValueError as e:
        # transformer does not support sparse data
        capitalized_lib = dataframe_lib.capitalize()
        error_message = str(e)
        assert (
            f"{capitalized_lib} output does not support sparse data." in error_message
            or "The transformer outputs a scipy sparse matrix." in error_message
        ), e
        return

    for case in outputs_default:
        _check_generated_dataframe(
            name,
            case,
            index,
            outputs_default[case],
            outputs_df[case],
            is_supported_dataframe,
            create_dataframe,
            assert_frame_equal,
        )
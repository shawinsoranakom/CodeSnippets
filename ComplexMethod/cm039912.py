def check_valid_tag_types(name, estimator):
    """Check that estimator tags are valid."""
    assert hasattr(estimator, "__sklearn_tags__"), (
        f"Estimator {name} does not have `__sklearn_tags__` method. This method is"
        " implemented in BaseEstimator and returns a sklearn.utils.Tags instance."
    )
    err_msg = (
        "Tag values need to be of a certain type. "
        "Please refer to the documentation of `sklearn.utils.Tags` for more details."
    )
    tags = get_tags(estimator)
    assert isinstance(tags.estimator_type, (str, type(None))), err_msg
    assert isinstance(tags.target_tags, TargetTags), err_msg
    assert isinstance(tags.classifier_tags, (ClassifierTags, type(None))), err_msg
    assert isinstance(tags.regressor_tags, (RegressorTags, type(None))), err_msg
    assert isinstance(tags.transformer_tags, (TransformerTags, type(None))), err_msg
    assert isinstance(tags.input_tags, InputTags), err_msg
    assert isinstance(tags.array_api_support, bool), err_msg
    assert isinstance(tags.no_validation, bool), err_msg
    assert isinstance(tags.non_deterministic, bool), err_msg
    assert isinstance(tags.requires_fit, bool), err_msg
    assert isinstance(tags._skip_test, bool), err_msg

    assert isinstance(tags.target_tags.required, bool), err_msg
    assert isinstance(tags.target_tags.one_d_labels, bool), err_msg
    assert isinstance(tags.target_tags.two_d_labels, bool), err_msg
    assert isinstance(tags.target_tags.positive_only, bool), err_msg
    assert isinstance(tags.target_tags.multi_output, bool), err_msg
    assert isinstance(tags.target_tags.single_output, bool), err_msg

    assert isinstance(tags.input_tags.pairwise, bool), err_msg
    assert isinstance(tags.input_tags.allow_nan, bool), err_msg
    assert isinstance(tags.input_tags.sparse, bool), err_msg
    assert isinstance(tags.input_tags.categorical, bool), err_msg
    assert isinstance(tags.input_tags.string, bool), err_msg
    assert isinstance(tags.input_tags.dict, bool), err_msg
    assert isinstance(tags.input_tags.one_d_array, bool), err_msg
    assert isinstance(tags.input_tags.two_d_array, bool), err_msg
    assert isinstance(tags.input_tags.three_d_array, bool), err_msg
    assert isinstance(tags.input_tags.positive_only, bool), err_msg

    if tags.classifier_tags is not None:
        assert isinstance(tags.classifier_tags.poor_score, bool), err_msg
        assert isinstance(tags.classifier_tags.multi_class, bool), err_msg
        assert isinstance(tags.classifier_tags.multi_label, bool), err_msg

    if tags.regressor_tags is not None:
        assert isinstance(tags.regressor_tags.poor_score, bool), err_msg

    if tags.transformer_tags is not None:
        assert isinstance(tags.transformer_tags.preserves_dtype, list), err_msg
def _yield_classifier_checks(classifier):
    _raise_for_missing_tags(classifier, "classifier_tags", ClassifierMixin)
    tags = get_tags(classifier)

    # test classifiers can handle non-array data and pandas objects
    yield check_classifier_data_not_an_array
    # test classifiers trained on a single label always return this label
    yield check_classifiers_one_label
    yield check_classifiers_one_label_sample_weights
    yield check_classifiers_classes
    yield check_estimators_partial_fit_n_features
    if tags.target_tags.multi_output:
        yield check_classifier_multioutput
    # basic consistency testing
    yield check_classifiers_train
    yield partial(check_classifiers_train, readonly_memmap=True)
    yield partial(check_classifiers_train, readonly_memmap=True, X_dtype="float32")
    yield check_classifiers_regression_target
    if tags.classifier_tags.multi_label:
        yield check_classifiers_multilabel_representation_invariance
        yield check_classifiers_multilabel_output_format_predict
        yield check_classifiers_multilabel_output_format_predict_proba
        yield check_classifiers_multilabel_output_format_decision_function
    if not tags.no_validation:
        yield check_supervised_y_no_nan
        if tags.target_tags.single_output:
            yield check_supervised_y_2d
    if "class_weight" in classifier.get_params().keys():
        yield check_class_weight_classifiers

    yield check_non_transformer_estimators_n_iter
    # test if predict_proba is a monotonic transformation of decision_function
    yield check_decision_proba_consistency

    if (
        isinstance(classifier, LinearClassifierMixin)
        and "class_weight" in classifier.get_params().keys()
    ):
        yield check_class_weight_balanced_linear_classifier

    if not tags.classifier_tags.multi_class:
        yield check_classifier_not_supporting_multiclass
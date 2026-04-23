def check_class_weight_classifiers(name, classifier_orig):
    if get_tags(classifier_orig).classifier_tags.multi_class:
        problems = [2, 3]
    else:  # binary classification only
        problems = [2]

    for n_centers in problems:
        # create a very noisy dataset
        X, y = make_blobs(centers=n_centers, random_state=0, cluster_std=20)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.5, random_state=0
        )

        # can't use gram_if_pairwise() here, setting up gram matrix manually
        if get_tags(classifier_orig).input_tags.pairwise:
            X_test = rbf_kernel(X_test, X_train)
            X_train = rbf_kernel(X_train, X_train)

        n_centers = len(np.unique(y_train))

        if n_centers == 2:
            class_weight = {0: 1000, 1: 0.0001}
        else:
            class_weight = {0: 1000, 1: 0.0001, 2: 0.0001}

        classifier = clone(classifier_orig).set_params(class_weight=class_weight)
        if hasattr(classifier, "n_iter"):
            classifier.set_params(n_iter=100)
        if hasattr(classifier, "max_iter"):
            classifier.set_params(max_iter=1000)
        if hasattr(classifier, "min_weight_fraction_leaf"):
            classifier.set_params(min_weight_fraction_leaf=0.01)
        if hasattr(classifier, "n_iter_no_change"):
            classifier.set_params(n_iter_no_change=20)

        set_random_state(classifier)
        classifier.fit(X_train, y_train)
        y_pred = classifier.predict(X_test)
        # XXX: Generally can use 0.89 here. On Windows, LinearSVC gets
        #      0.88 (Issue #9111)
        if not get_tags(classifier_orig).classifier_tags.poor_score:
            assert np.mean(y_pred == 0) > 0.87
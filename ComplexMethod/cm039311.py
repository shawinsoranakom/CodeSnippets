def _get_instance_with_pipeline(meta_estimator, init_params):
    """Given a single meta-estimator instance, generate an instance with a pipeline"""
    if {"estimator", "base_estimator", "regressor"} & init_params:
        if is_regressor(meta_estimator):
            estimator = make_pipeline(TfidfVectorizer(), Ridge())
            param_grid = {"ridge__alpha": [0.1, 1.0]}
        else:
            estimator = make_pipeline(TfidfVectorizer(), LogisticRegression())
            param_grid = {"logisticregression__C": [0.1, 1.0]}

        if init_params.intersection(
            {"param_grid", "param_distributions"}
        ):  # SearchCV estimators
            extra_params = {"n_iter": 2} if "n_iter" in init_params else {}
            return type(meta_estimator)(estimator, param_grid, **extra_params)
        else:
            return type(meta_estimator)(estimator)

    if "transformer_list" in init_params:
        # FeatureUnion
        transformer_list = [
            ("trans1", make_pipeline(TfidfVectorizer(), MaxAbsScaler())),
            (
                "trans2",
                make_pipeline(TfidfVectorizer(), StandardScaler(with_mean=False)),
            ),
        ]
        return type(meta_estimator)(transformer_list)

    if "estimators" in init_params:
        # stacking, voting
        if is_regressor(meta_estimator):
            estimator = [
                ("est1", make_pipeline(TfidfVectorizer(), Ridge(alpha=0.1))),
                ("est2", make_pipeline(TfidfVectorizer(), Ridge(alpha=1))),
            ]
        else:
            estimator = [
                (
                    "est1",
                    make_pipeline(TfidfVectorizer(), LogisticRegression(C=0.1)),
                ),
                ("est2", make_pipeline(TfidfVectorizer(), LogisticRegression(C=1))),
            ]
        return type(meta_estimator)(estimator)
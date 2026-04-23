def train_and_evaluate_models(
        self,
        datasets,
        max_depths,
        min_samples_leafs,
        criterion_list,
        feature_columns,
        ranking=False,
    ):
        """
        Does a grid search over max_depths, min_samples_leafs, and criterion_list and returns the best model.
        """

        results = []
        best_model = None
        best_model_safe_proba = 0
        best_model_num_correct = 0
        best_model_unsafe_leaves = []
        columns = ["set", "crit", "max_depth", "min_samples_leaf"]
        metrics_columns = []
        for max_depth, min_samples_leaf, criterion in itertools.product(
            max_depths, min_samples_leafs, criterion_list
        ):
            print(
                f"max_depth={max_depth} min_samples_leaf={min_samples_leaf} criterion={criterion}"
            )
            model = DecisionTreeClassifier(
                max_depth=max_depth,
                min_samples_leaf=min_samples_leaf,
                criterion=criterion,
                random_state=42,
            )
            df_train = datasets["train"]
            df_val = datasets["val"]
            if ranking:
                model.fit(
                    df_train[feature_columns],
                    df_train["winner"],
                    sample_weight=df_train["relative_performance"],
                )
            else:
                model.fit(df_train[feature_columns], df_train["winner"])

            model = DecisionTree(model, feature_columns)

            if ranking:
                model.prune(df_train, "winner", k=self.ranking_num_choices())

            unsafe_leaves = self.get_unsafe_leaves(model, df_train, feature_columns)
            predictions, proba, leaf_ids = self.predict(model, df_val, feature_columns)

            wrong_pct = self.get_allowed_wrong_prediction_pct()
            evaluator = DecisionEvaluator(
                self,
                model,
                predictions,
                df_val,
                proba,
                wrong_pct=wrong_pct,
                unsafe_leaves=unsafe_leaves,
                leaf_ids=leaf_ids,
                k=self.ranking_num_choices(),
                ranking=ranking,
            )
            safe_proba = evaluator.get_safe_proba()
            print(f"safe_proba={safe_proba}")

            def eval(name, df):
                if ranking:
                    # when ranking is enabled, we duplicate each input for each choice that
                    # is almost as good as the best choice
                    # we do not want to evaluate the same input multiple times, so we remove duplicates here
                    df = df[df["winner"] == df["actual_winner"]]
                predictions, proba, leaf_ids = self.predict(model, df, feature_columns)
                evaluator = DecisionEvaluator(
                    self,
                    model,
                    predictions,
                    df,
                    proba,
                    wrong_pct=wrong_pct,
                    threshold=safe_proba,
                    unsafe_leaves=unsafe_leaves,
                    leaf_ids=leaf_ids,
                    k=self.ranking_num_choices(),
                    ranking=ranking,
                )
                return evaluator.get_results()

            for dataset_name, dataset in datasets.items():
                eval_result: EvalResults = eval(dataset_name, dataset)
                eval_result_metrics = eval_result.to_map()
                if dataset_name == "val":
                    num_correct = eval_result.accuracy.num_correct
                    num_wrong = eval_result.accuracy.num_wrong
                    num_total = eval_result.accuracy.total
                    if num_wrong <= num_total * wrong_pct:
                        if num_correct > best_model_num_correct:
                            print(
                                f"new best model with {num_correct} correct and {num_wrong} wrong"
                            )
                            best_model = model
                            best_model_num_correct = num_correct
                            best_model_safe_proba = safe_proba
                            best_model_unsafe_leaves = unsafe_leaves

                result = (dataset_name, criterion, max_depth, min_samples_leaf)
                result += tuple(eval_result_metrics.values())
                results.append(result)
                if len(metrics_columns) == 0:
                    metrics_columns = list(eval_result_metrics.keys())
                    columns += metrics_columns

        return (
            pd.DataFrame(results, columns=columns),
            best_model,
            best_model_safe_proba,
            best_model_unsafe_leaves,
        )
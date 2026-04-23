def __sklearn_tags__(self):
        tags = super().__sklearn_tags__()

        if not self.steps:
            return tags

        try:
            if self.steps[0][1] is not None and self.steps[0][1] != "passthrough":
                tags.input_tags.pairwise = get_tags(
                    self.steps[0][1]
                ).input_tags.pairwise
            # WARNING: the sparse tag can be incorrect.
            # Some Pipelines accepting sparse data are wrongly tagged sparse=False.
            # For example Pipeline([PCA(), estimator]) accepts sparse data
            # even if the estimator doesn't as PCA outputs a dense array.
            tags.input_tags.sparse = all(
                get_tags(step).input_tags.sparse
                for name, step in self.steps
                if step is not None and step != "passthrough"
            )
        except (ValueError, AttributeError, TypeError):
            # This happens when the `steps` is not a list of (name, estimator)
            # tuples and `fit` is not called yet to validate the steps.
            pass

        try:
            if self.steps[-1][1] is not None and self.steps[-1][1] != "passthrough":
                last_step_tags = get_tags(self.steps[-1][1])
                tags.estimator_type = last_step_tags.estimator_type
                tags.target_tags.multi_output = last_step_tags.target_tags.multi_output
                tags.classifier_tags = deepcopy(last_step_tags.classifier_tags)
                tags.regressor_tags = deepcopy(last_step_tags.regressor_tags)
                tags.transformer_tags = deepcopy(last_step_tags.transformer_tags)
        except (ValueError, AttributeError, TypeError):
            # This happens when the `steps` is not a list of (name, estimator)
            # tuples and `fit` is not called yet to validate the steps.
            pass

        return tags
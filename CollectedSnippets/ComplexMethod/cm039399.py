def _check_algorithm_metric(self):
        if self.algorithm == "auto":
            if self.metric == "precomputed":
                alg_check = "brute"
            elif (
                callable(self.metric)
                or self.metric in VALID_METRICS["ball_tree"]
                or isinstance(self.metric, DistanceMetric)
            ):
                alg_check = "ball_tree"
            else:
                alg_check = "brute"
        else:
            alg_check = self.algorithm

        if callable(self.metric):
            if self.algorithm == "kd_tree":
                # callable metric is only valid for brute force and ball_tree
                raise ValueError(
                    "kd_tree does not support callable metric '%s'"
                    "Function call overhead will result"
                    "in very poor performance." % self.metric
                )
        elif self.metric not in VALID_METRICS[alg_check] and not isinstance(
            self.metric, DistanceMetric
        ):
            raise ValueError(
                "Metric '%s' not valid. Use "
                "sorted(sklearn.neighbors.VALID_METRICS['%s']) "
                "to get valid options. "
                "Metric can also be a callable function." % (self.metric, alg_check)
            )

        if self.metric_params is not None and "p" in self.metric_params:
            if self.p is not None:
                warnings.warn(
                    (
                        "Parameter p is found in metric_params. "
                        "The corresponding parameter from __init__ "
                        "is ignored."
                    ),
                    SyntaxWarning,
                    stacklevel=3,
                )
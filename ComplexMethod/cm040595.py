def result(self):
        if (
            self.curve == metrics_utils.AUCCurve.PR
            and self.summation_method
            == metrics_utils.AUCSummationMethod.INTERPOLATION
        ):
            # This use case is different and is handled separately.
            return self.interpolate_pr_auc()

        # Set `x` and `y` values for the curves based on `curve` config.
        recall = ops.divide_no_nan(
            self.true_positives,
            ops.add(self.true_positives, self.false_negatives),
        )
        if self.curve == metrics_utils.AUCCurve.ROC:
            fp_rate = ops.divide_no_nan(
                self.false_positives,
                ops.add(self.false_positives, self.true_negatives),
            )
            x = fp_rate
            y = recall
        elif self.curve == metrics_utils.AUCCurve.PR:  # curve == 'PR'.
            precision = ops.divide_no_nan(
                self.true_positives,
                ops.add(self.true_positives, self.false_positives),
            )
            x = recall
            y = precision
        else:  # curve == 'PRGAIN'.
            # Due to the hyperbolic transform, this formula is less robust than
            # ROC and PR values. In particular
            # 1) Both measures diverge when there are no negative values;
            # 2) Both measures diverge when there are no true positives;
            # 3) Recall gain becomes negative when the recall is lower than the
            #    label average (i.e. when more negative examples are
            #    classified positive than real positives).
            #
            # We ignore case 1 as it is easily understood that metrics would be
            # badly defined then. For case 2 we set recall_gain to 0 and
            # precision_gain to 1. For case 3 we set recall_gain to 0. These
            # fixes will result in an overestimation of the AUC for estimators
            # that are anti-correlated with the label (at some threshold).

            # The scaling factor $\frac{P}{N}$ that is used to for both gain
            # values.
            scaling_factor = ops.divide_no_nan(
                ops.add(self.true_positives, self.false_negatives),
                ops.add(self.true_negatives, self.false_positives),
            )

            recall_gain = 1.0 - scaling_factor * ops.divide_no_nan(
                self.false_negatives, self.true_positives
            )
            precision_gain = 1.0 - scaling_factor * ops.divide_no_nan(
                self.false_positives, self.true_positives
            )
            # Handle case 2.
            recall_gain = ops.where(
                ops.equal(self.true_positives, 0.0), 0.0, recall_gain
            )
            precision_gain = ops.where(
                ops.equal(self.true_positives, 0.0), 1.0, precision_gain
            )
            # Handle case 3.
            recall_gain = ops.maximum(recall_gain, 0.0)

            x = recall_gain
            y = precision_gain

        # Find the rectangle heights based on `summation_method`.
        if (
            self.summation_method
            == metrics_utils.AUCSummationMethod.INTERPOLATION
        ):
            # Note: the case ('PR', 'interpolation') has been handled above.
            heights = ops.divide(
                ops.add(y[: self.num_thresholds - 1], y[1:]), 2.0
            )
        elif self.summation_method == metrics_utils.AUCSummationMethod.MINORING:
            heights = ops.minimum(y[: self.num_thresholds - 1], y[1:])
        # self.summation_method = metrics_utils.AUCSummationMethod.MAJORING:
        else:
            heights = ops.maximum(y[: self.num_thresholds - 1], y[1:])

        # Sum up the areas of all the rectangles.
        riemann_terms = ops.multiply(
            ops.subtract(x[: self.num_thresholds - 1], x[1:]), heights
        )
        if self.multi_label:
            by_label_auc = ops.sum(riemann_terms, axis=0)

            if self.label_weights is None:
                # Unweighted average of the label AUCs.
                return ops.mean(by_label_auc)
            else:
                # Weighted average of the label AUCs.
                return ops.divide_no_nan(
                    ops.sum(ops.multiply(by_label_auc, self.label_weights)),
                    ops.sum(self.label_weights),
                )
        else:
            return ops.sum(riemann_terms)
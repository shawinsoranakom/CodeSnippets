def build(self, y_true, y_pred):
        num_outputs = len(tree.flatten(y_pred))
        # By "flat" we mean not deeply nested, like a single list or dict.
        y_pred_is_flat = tree.is_nested(y_pred) and len(y_pred) == num_outputs

        # When outputs is a dict, prefer those keys over the ouput names.
        if y_pred_is_flat and isinstance(y_pred, dict):
            if self.output_names and set(y_pred.keys()) == set(
                self.output_names
            ):
                # If there is a perfect match, use the model output order.
                output_names = self.output_names
            elif isinstance(y_pred, OrderedDict):
                output_names = list(y_pred.keys())
            else:
                output_names = sorted(list(y_pred.keys()))
        else:
            output_names = self.output_names

        # `self._resolved_output_names` is for `_flatten_y`. It can only be
        # used if `y_pred` is not deeply nested and is useless for 1 output.
        if num_outputs > 1 and y_pred_is_flat:
            self._resolved_output_names = output_names
        else:
            self._resolved_output_names = None

        # We still pass `output_names` even if they are not used for
        # `self._resolved_output_names` in order to name metrics.
        self._flat_metrics = self._build_metrics_set(
            self._user_metrics,
            num_outputs,
            output_names,
            y_true,
            y_pred,
            y_pred_is_flat,
            argument_name="metrics",
        )
        self._flat_weighted_metrics = self._build_metrics_set(
            self._user_weighted_metrics,
            num_outputs,
            output_names,
            y_true,
            y_pred,
            y_pred_is_flat,
            argument_name="weighted_metrics",
        )
        self.built = True
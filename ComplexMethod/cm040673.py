def _build_metrics_set(
        self,
        metrics,
        num_outputs,
        output_names,
        y_true,
        y_pred,
        y_pred_is_flat,
        argument_name,
    ):
        if not metrics:
            return [None] * num_outputs

        if num_outputs == 1:
            # Single output, all metrics apply to it, don't use `output_names`.
            return [
                get_metrics_list(
                    tree.flatten(metrics),
                    tree.flatten(y_true)[0],
                    tree.flatten(y_pred)[0],
                    None,
                )
            ]

        flat_metrics = None
        if y_pred_is_flat:
            if (
                isinstance(metrics, (list, tuple))
                and len(metrics) == num_outputs
            ):
                # `metrics` is a list with one entry per output.
                flat_metrics = metrics

            elif (
                output_names
                and isinstance(metrics, dict)
                and len(metrics) <= num_outputs
                and set(metrics.keys()) <= set(output_names)
            ):
                # Flatten `metrics` with the correct flattening order.
                flat_metrics = [
                    metrics[name] if name in metrics else None
                    for name in output_names
                ]

        # Flat case: one list or dict of metrics.
        if flat_metrics is not None:
            try:
                return [
                    get_metrics_list(m, yt, yp, n)
                    for m, yt, yp, n in zip(
                        flat_metrics,
                        self._flatten_y(y_true),
                        self._flatten_y(y_pred),
                        output_names if output_names else [None] * num_outputs,
                    )
                ]
            except ValueError as e:
                raise ValueError(
                    f"{e}\nReceived: {argument_name}={metrics}"
                ) from e

        try:
            # Deeply nested case: `metrics` must have the structure of `y_pred`,
            # `y_pred` and `y_true` must also have the same nested structure.
            # Note that the tree API wants exact matches, lists and tuples are
            # not considered equivalent, so we have to turn them all to tuples.
            tuples_y_pred = tree.lists_to_tuples(y_pred)

            # `output_names` came from the model and is a flattened version of
            # the output structure using the `y_pred` flattening order.
            output_names_struct = tree.pack_sequence_as(
                tuples_y_pred,
                output_names if output_names else [None] * num_outputs,
            )
            return tree.flatten(
                tree.map_structure_up_to(
                    tuples_y_pred,
                    get_metrics_list,
                    tree.lists_to_tuples(metrics),
                    tree.lists_to_tuples(y_true),
                    tuples_y_pred,
                    output_names_struct,
                )
            )
        except (ValueError, TypeError) as e:
            # A ValueError from `get_metrics_list` or a ValueError / TypeError
            # from `tree.map_structure_up_to` for mismatched structures.
            # The use of `self.output_names` instead of `output_names` is
            # intentional; we want the true output names, the output keys will
            # be shown as part of printing `y_pred`.
            if self.output_names:
                raise ValueError(
                    f"{e}\nInvalid `{argument_name}`. `{argument_name}` should "
                    "contain metrics objects and either be a dict or a list "
                    "matching the output names of the functional model "
                    f"{self.output_names} or match the output structure of "
                    f"the model: {tree.map_structure(lambda _: 'X', y_pred)}.\n"
                    f"Received: {argument_name}={metrics}"
                ) from e
            else:
                raise ValueError(
                    f"{e}\nInvalid `{argument_name}`. `{argument_name}` should "
                    "contain metrics objects and match the output structure of "
                    f"the model: {tree.map_structure(lambda _: 'X', y_pred)}.\n"
                    f"Received: {argument_name}={metrics}"
                ) from e
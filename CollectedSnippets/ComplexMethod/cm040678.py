def call(self, y_true, y_pred, sample_weight=None):
        def resolve_path(path, object):
            for _path in path:
                object = object[_path]
            return object

        if not tree.is_nested(y_true) and not tree.is_nested(y_pred):
            # Fast path: single output case / no loss-tracking metric.
            if not self.built:
                self.build(y_true, y_pred)
            # Although we are in the fast path, we still need to iterate
            # through the losses to prevent the torch compiler from failing.
            loss_values = []
            for path, loss_fn, loss_weight, _ in self._flat_losses:
                y_t, y_p = (
                    resolve_path(path, y_true),
                    resolve_path(path, y_pred),
                )
                if sample_weight is not None and tree.is_nested(sample_weight):
                    _sample_weight = resolve_path(path, sample_weight)
                else:
                    _sample_weight = sample_weight
                value = ops.cast(
                    loss_fn(y_t, y_p, _sample_weight), dtype=self.dtype
                )
                if loss_weight is not None:
                    value = ops.multiply(value, loss_weight)
                loss_values.append(value)
            return loss_values[0]

        try:
            tree.assert_same_structure(y_pred, y_true)
        except ValueError:
            # Check case where y_true is either flat or leaf
            if (
                not tree.is_nested(y_true)
                and hasattr(y_pred, "__len__")
                and len(y_pred) == 1
            ):
                y_true = [y_true]

            # Check case where y_pred is list/tuple and y_true is dict
            elif isinstance(y_pred, (list, tuple)) and isinstance(y_true, dict):
                if set(self.output_names) == set(y_true.keys()):
                    y_true = [y_true[name] for name in self.output_names]

            try:
                y_true = tree.pack_sequence_as(y_pred, y_true)
            except:
                # Check case where y_true has the same structure but uses
                # different (but reconcilable) container types,
                # e.g `list` vs `tuple`.
                try:
                    tree.assert_same_paths(y_true, y_pred)
                    y_true = tree.pack_sequence_as(y_pred, tree.flatten(y_true))
                except:
                    try:
                        # Check case where loss is partially defined over y_pred
                        flat_y_true = tree.flatten(y_true)
                        flat_loss = tree.flatten(self._user_loss)
                        flat_loss_non_nones = [
                            (i, loss)
                            for i, loss in enumerate(flat_loss)
                            if loss is not None
                        ]
                        if len(flat_y_true) != len(flat_loss_non_nones):
                            raise ValueError(
                                "Internal error: the number of values in "
                                f"`y_true` ({len(flat_y_true)}) must match the "
                                "number of non-None values in `loss` "
                                f"({len(flat_loss_non_nones)})."
                            )
                        y_true = [None] * len(flat_loss)
                        for y_t, (i, loss) in zip(
                            flat_y_true, flat_loss_non_nones
                        ):
                            y_true[i] = y_t
                        y_true = tree.pack_sequence_as(self._user_loss, y_true)
                    except:
                        y_true_struct = tree.map_structure(
                            lambda _: "*", y_true
                        )
                        y_pred_struct = tree.map_structure(
                            lambda _: "*", y_pred
                        )
                        raise ValueError(
                            "y_true and y_pred have different structures.\n"
                            f"y_true: {y_true_struct}\n"
                            f"y_pred: {y_pred_struct}\n"
                        )

        if not self.built:
            self.build(y_true, y_pred)

        try:
            tree.assert_same_structure(self._y_pred_build_structure, y_pred)
        except ValueError:
            y_pred = tree.pack_sequence_as(
                self._y_pred_build_structure, tree.flatten(y_pred)
            )
        try:
            tree.assert_same_structure(self._y_true_build_structure, y_true)
        except ValueError:
            y_true = tree.pack_sequence_as(
                self._y_true_build_structure, tree.flatten(y_true)
            )

        # We need to add a dummy `None` if the model has only a single output.
        metrics = [None] if len(self.metrics) == 0 else self.metrics

        # Iterate all losses in flat form.
        loss_values = []

        for (path, loss_fn, loss_weight, _), metric in zip(
            self._flat_losses, metrics
        ):
            y_t, y_p = resolve_path(path, y_true), resolve_path(path, y_pred)
            if sample_weight is not None and tree.is_nested(sample_weight):
                _sample_weight = resolve_path(path, sample_weight)
            else:
                _sample_weight = sample_weight

            value = ops.cast(
                loss_fn(y_t, y_p, _sample_weight), dtype=self.dtype
            )
            # Record *unweighted* individual losses.
            if metric:
                metric.update_state(
                    loss_module.unscale_loss_for_distribution(value),
                    sample_weight=tree.flatten(y_p)[0].shape[0],
                )
            if loss_weight is not None:
                value = ops.multiply(value, loss_weight)
            loss_values.append(value)

        if loss_values:
            total_loss = sum(loss_values)
            return total_loss
        return None
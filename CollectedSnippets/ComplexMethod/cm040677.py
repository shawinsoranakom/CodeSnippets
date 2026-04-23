def build(self, y_true, y_pred):
        loss = self._user_loss
        loss_weights = self._user_loss_weights
        flat_output_names = self.output_names
        if (
            self.output_names
            and isinstance(self._user_loss, dict)
            and not isinstance(y_pred, dict)
        ):
            if set(self.output_names) == set(self._user_loss.keys()):
                loss = [self._user_loss[name] for name in self.output_names]
                if isinstance(self._user_loss_weights, dict):
                    loss_weights = [
                        self._user_loss_weights[name]
                        for name in self.output_names
                    ]
            else:
                raise ValueError(
                    f"Expected keys {self.output_names} in loss dict, but "
                    f"found loss.keys()={list(self._user_loss.keys())}"
                )

        # Pytree leaf container
        class WeightedLoss:
            def __new__(cls, loss, weight):
                if loss is None:
                    return None
                return object.__new__(cls)

            def __init__(self, loss, weight):
                self.loss = loss
                self.weight = weight

        # pack the losses and the weights together
        if loss_weights is not None:
            try:
                tree.assert_same_structure(loss, loss_weights)
            except ValueError:
                flat_loss_weights = tree.flatten(loss_weights)
                if len(tree.flatten(loss)) != len(flat_loss_weights):
                    raise ValueError(
                        f"`loss_weights` must match the number of losses, "
                        f"got {len(tree.flatten(loss))} losses "
                        f"and {len(loss_weights)} weights."
                    )
                loss_weights = tree.pack_sequence_as(loss, flat_loss_weights)
            loss = tree.map_structure(
                lambda _loss, _weight: WeightedLoss(_loss, _weight),
                loss,
                loss_weights,
            )
        else:
            loss = tree.map_structure(
                lambda _loss: WeightedLoss(_loss, None), loss
            )

        self._flat_losses = []

        if (
            isinstance(loss, dict)
            and issubclass(type(y_pred), (list, tuple))
            and set(loss.keys()) == set(flat_output_names)
            and len(y_pred) == len(flat_output_names)
        ):
            y_pred = {name: y_p for name, y_p in zip(flat_output_names, y_pred)}
            y_true = {name: y_t for name, y_t in zip(flat_output_names, y_true)}
        elif (
            isinstance(loss, dict)
            and not tree.is_nested(y_pred)
            and set(loss.keys()) == set(flat_output_names)
            and len(flat_output_names) == 1
        ):
            y_pred = {
                name: y_p for name, y_p in zip(flat_output_names, [y_pred])
            }
            y_true = {
                name: y_t for name, y_t in zip(flat_output_names, [y_true])
            }

        try:
            output_names = tree.pack_sequence_as(y_pred, flat_output_names)
        except:
            inferred_flat_output_names = self._get_y_pred_output_names(y_pred)
            output_names = tree.pack_sequence_as(
                y_pred, inferred_flat_output_names
            )

        if not tree.is_nested(loss):
            loss = tree.map_structure(lambda x: loss, y_pred)

        self._build_nested(y_true, y_pred, loss, output_names, ())

        # Add `Mean` metric to the tracker for each loss.
        if len(self._flat_losses) > 1:
            for _loss in self._flat_losses:
                name = f"{_loss.name}_loss"
                self._tracker.add_to_store(
                    "metrics", metrics_module.Mean(name=name)
                )

        self._y_pred_build_structure = tree.map_structure(
            lambda x: None, y_pred
        )
        self._y_true_build_structure = tree.map_structure(
            lambda x: None, y_true
        )
        self.built = True
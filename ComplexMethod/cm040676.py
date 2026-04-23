def _build_nested(self, y_true, y_pred, loss, output_names, current_path):
        flat_y_pred = tree.flatten(y_pred)
        if not tree.is_nested(loss):
            _loss = loss.loss
            if _loss is None:
                return
            loss_weight = loss.weight
            resolved_loss = get_loss(_loss, y_true, y_pred)
            name_path = current_path
            if not tree.is_nested(output_names):
                if output_names is not None:
                    output_name = output_names
                else:
                    output_name = resolved_loss.name
                if len(name_path) == 0:
                    name_path = (output_name,)
                elif isinstance(name_path[-1], int):
                    name_path = name_path[:-1] + (output_name,)
            name = "/".join([str(path) for path in name_path])
            if name == "":
                if isinstance(output_names, dict):
                    flat_output_names = list(output_names.keys())
                else:
                    flat_output_names = tree.flatten(output_names)
                name = "_".join(flat_output_names)
            self._flat_losses.append(
                CompileLoss.Loss(current_path, resolved_loss, loss_weight, name)
            )
            return
        elif (
            issubclass(type(loss), (list, tuple))
            and all([not tree.is_nested(_loss) for _loss in loss])
            and len(loss) == len(flat_y_pred)
        ):
            loss = tree.pack_sequence_as(y_pred, loss)
        elif issubclass(type(loss), (list, tuple)) and not isinstance(
            y_pred, type(loss)
        ):
            for _loss in loss:
                self._build_nested(
                    y_true,
                    y_pred,
                    _loss,
                    output_names,
                    current_path,
                )
            return

        if not tree.is_nested(loss):
            return self._build_nested(
                y_true, y_pred, loss, output_names, current_path
            )

        if not isinstance(loss, type(y_pred)):
            raise KeyError(
                f"The path: {current_path} in "
                "the `loss` argument, can't be found in "
                "the model's output (`y_pred`)."
            )

        # shallow traverse the loss config
        if isinstance(loss, dict):
            iterator = loss.items()

            def key_check_fn(key, objs):
                return all(
                    [isinstance(obj, dict) and key in obj for obj in objs]
                )

        elif issubclass(type(loss), (list, tuple)):
            iterator = enumerate(loss)

            def key_check_fn(key, objs):
                return all(
                    [
                        issubclass(type(obj), (list, tuple)) and key < len(obj)
                        for obj in objs
                    ]
                )

        else:
            raise TypeError(
                f"Unsupported type {type(loss)} in the `loss` configuration."
            )

        for key, _loss in iterator:
            if _loss is None:
                continue
            if not key_check_fn(key, (y_true, y_pred)):
                raise KeyError(
                    f"The path: {current_path + (key,)} in "
                    "the `loss` argument, can't be found in "
                    "either the model's output (`y_pred`) or in the "
                    "labels (`y_true`)."
                )

            self._build_nested(
                y_true[key],
                y_pred[key],
                _loss,
                output_names[key],
                current_path + (key,),
            )
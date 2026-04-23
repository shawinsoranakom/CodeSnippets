def compute_loss(
        self, x=None, y=None, y_pred=None, sample_weight=None, training=True
    ):
        """Compute combined distillation loss.

        Arguments:
            x: Input data.
            y: Target data.
            y_pred: Model predictions.
            sample_weight: Sample weights (currently unused).
            training: Whether the model is in training mode.

        Returns:
            Combined loss tensor.
        """
        # Handle case where y_pred is not provided
        if y_pred is None:
            y_pred = self(x, training=training)
        # Compute student loss
        student_loss = 0.0
        if self.student_loss_weight > 0.0 and y is not None:
            loss_values = tree.map_structure(
                lambda l, o, o_pred: l(o, o_pred),
                self._student_loss,
                y,
                y_pred,
            )
            flat_losses = tree.flatten(loss_values)
            student_loss = (
                keras.ops.sum(keras.ops.stack(flat_losses))
                if len(flat_losses) > 1
                else flat_losses[0]
            )

            # Ensure student_loss is a scalar
            if hasattr(student_loss, "shape") and len(student_loss.shape) > 0:
                student_loss = keras.ops.mean(student_loss)

        # Compute distillation loss
        distillation_loss = 0.0
        if self.student_loss_weight < 1.0:
            teacher_features = self._extract_all_teacher_features(x)
            student_features = self._extract_all_student_features(x, y_pred)

            # Apply distillation losses using pre-extracted features
            for distillation_loss_fn, weight in zip(
                self.distillation_losses, self.distillation_loss_weights
            ):
                # Get appropriate outputs/features for this distillation loss
                if (
                    hasattr(distillation_loss_fn, "teacher_layer_name")
                    and distillation_loss_fn.teacher_layer_name is not None
                ):
                    # FeatureDistillation with specific layers
                    try:
                        distillation_loss_teacher_output = (
                            self._get_distillation_loss_features(
                                distillation_loss_fn,
                                teacher_features,
                                is_teacher=True,
                            )
                        )
                        distillation_loss_student_output = (
                            self._get_distillation_loss_features(
                                distillation_loss_fn,
                                student_features,
                                is_teacher=False,
                            )
                        )
                    except ValueError as e:
                        # Re-raise with context about which loss failed
                        raise RuntimeError(
                            f"Failed to extract features for "
                            f"{type(distillation_loss_fn).__name__} "
                            f"targeting teacher layer "
                            f"'{distillation_loss_fn.teacher_layer_name}' "
                            f"and student layer "
                            f"'{distillation_loss_fn.student_layer_name}'. "
                            f"Original error: {e}"
                        ) from e
                else:
                    # LogitsDistillation or FeatureDistillation (final outputs)
                    distillation_loss_teacher_output = teacher_features[
                        "final_output"
                    ]
                    distillation_loss_student_output = y_pred

                # Validate outputs are compatible for this distillation loss
                distillation_loss_fn.validate_outputs(
                    distillation_loss_teacher_output,
                    distillation_loss_student_output,
                )

                # Compute loss for this distillation loss
                current_distillation_loss = distillation_loss_fn.compute_loss(
                    distillation_loss_teacher_output,
                    distillation_loss_student_output,
                )

                # Validate that distillation loss returns a scalar
                if (
                    hasattr(current_distillation_loss, "shape")
                    and len(current_distillation_loss.shape) > 0
                ):
                    raise ValueError(
                        f"Distillation loss "
                        f"{distillation_loss_fn.__class__.__name__} "
                        f"returned a non-scalar loss with shape "
                        f"{current_distillation_loss.shape}. "
                        f"The compute_loss method must return a scalar "
                        f"tensor."
                    )

                # Apply weight and add to total
                distillation_loss = keras.ops.add(
                    distillation_loss,
                    keras.ops.multiply(weight, current_distillation_loss),
                )

        # Combine losses
        total_loss = keras.ops.add(
            keras.ops.multiply(self.student_loss_weight, student_loss),
            keras.ops.multiply(
                keras.ops.subtract(1.0, self.student_loss_weight),
                distillation_loss,
            ),
        )

        # Update metrics
        self.student_loss_tracker.update_state(student_loss)
        self.distillation_loss_tracker.update_state(distillation_loss)
        self.total_loss_tracker.update_state(total_loss)

        return total_loss
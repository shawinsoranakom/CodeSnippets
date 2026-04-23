def __init__(
        self,
        teacher,
        student,
        distillation_losses,
        distillation_loss_weights=None,
        student_loss_weight=0.5,
        name="distiller",
        **kwargs,
    ):
        super().__init__(name=name, **kwargs)

        # Validate inputs
        self._validate_models(teacher, student)

        # Store configuration
        self.teacher = teacher
        self.student = student

        # Validate student_loss_weight
        if not isinstance(student_loss_weight, (int, float)):
            raise ValueError(
                f"student_loss_weight must be a number, got "
                f"{type(student_loss_weight)}"
            )
        if student_loss_weight < 0.0 or student_loss_weight > 1.0:
            raise ValueError(
                f"student_loss_weight must be between 0.0 and 1.0, "
                f"got {student_loss_weight}"
            )
        self.student_loss_weight = student_loss_weight

        # Handle distillation losses configuration
        if distillation_losses is None:
            raise ValueError(
                "'distillation_losses' cannot be `None`. Provide a "
                "distillation loss (e.g., LogitsDistillation or "
                "FeatureDistillation) or a list of distillation losses."
            )

        # Convert single distillation loss to list for uniform handling
        if not isinstance(distillation_losses, (list, tuple)):
            self.distillation_losses = [distillation_losses]
            self.distillation_loss_weights = [1.0]
        else:
            self.distillation_losses = distillation_losses
            # Set default weights if not provided
            if distillation_loss_weights is None:
                self.distillation_loss_weights = [1.0] * len(
                    distillation_losses
                )
            else:
                if len(distillation_loss_weights) != len(distillation_losses):
                    raise ValueError(
                        f"Number of distillation_loss_weights "
                        f"({len(distillation_loss_weights)}) must match "
                        f"number of distillation_losses "
                        f"({len(distillation_losses)})"
                    )
                self.distillation_loss_weights = distillation_loss_weights

        # Validate distillation loss compatibility and create extractors
        for distillation_loss in self.distillation_losses:
            self._validate_distillation_loss_compatibility(
                teacher, student, distillation_loss
            )

        self._create_multi_feature_extractors()

        # Freeze teacher model
        self.teacher.trainable = False

        # Initialize loss tracking metrics
        self.student_loss_tracker = keras.metrics.Mean(name="student_loss")
        self.distillation_loss_tracker = keras.metrics.Mean(
            name="distillation_loss"
        )
        self.total_loss_tracker = keras.metrics.Mean(name="total_loss")
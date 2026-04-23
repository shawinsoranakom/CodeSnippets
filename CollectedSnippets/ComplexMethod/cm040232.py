def validate_model_compatibility(self, teacher, student):
        """Validate that teacher and student models are compatible for feature
        distillation."""
        if (
            self.teacher_layer_name is not None
            or self.student_layer_name is not None
        ):
            teacher_is_subclassed = (
                not hasattr(teacher, "inputs") or teacher.inputs is None
            )
            student_is_subclassed = (
                not hasattr(student, "inputs") or student.inputs is None
            )

            if teacher_is_subclassed or student_is_subclassed:
                subclassed_models = []
                if teacher_is_subclassed:
                    subclassed_models.append("teacher")
                if student_is_subclassed:
                    subclassed_models.append("student")

                models_str = " and ".join(subclassed_models)
                raise ValueError(
                    f"FeatureDistillation with specific layer names requires "
                    f"Functional or Sequential models. The {models_str} "
                    f"model(s) appear to be subclassed (no symbolic "
                    f"inputs/outputs). Either use Functional/Sequential "
                    f"models, or use FeatureDistillation without layer names "
                    f"(to distill final outputs only), or use "
                    f"LogitsDistillation instead."
                )

        if self.teacher_layer_name is not None:
            try:
                teacher.get_layer(name=self.teacher_layer_name)
            except ValueError as e:
                raise ValueError(f"In teacher model: {e}")

        if self.student_layer_name is not None:
            try:
                student.get_layer(name=self.student_layer_name)
            except ValueError as e:
                raise ValueError(f"In student model: {e}")
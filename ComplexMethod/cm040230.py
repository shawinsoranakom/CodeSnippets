def _create_multi_feature_extractors(self):
        """Create feature extractors for efficient multi-layer extraction."""
        teacher_layer_names = []
        student_layer_names = []

        for distillation_loss in self.distillation_losses:
            if (
                hasattr(distillation_loss, "teacher_layer_name")
                and distillation_loss.teacher_layer_name
            ):
                if (
                    distillation_loss.teacher_layer_name
                    not in teacher_layer_names
                ):
                    teacher_layer_names.append(
                        distillation_loss.teacher_layer_name
                    )
            if (
                hasattr(distillation_loss, "student_layer_name")
                and distillation_loss.student_layer_name
            ):
                if (
                    distillation_loss.student_layer_name
                    not in student_layer_names
                ):
                    student_layer_names.append(
                        distillation_loss.student_layer_name
                    )

        self._teacher_feature_extractor = self._create_feature_extractor(
            self.teacher, teacher_layer_names
        )
        self._student_feature_extractor = self._create_feature_extractor(
            self.student, student_layer_names
        )
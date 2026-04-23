def _execute_global_transforms(self) -> tuple[dict, dict]:
        node_template = self._change_set.update_model.node_template

        transform_delta: PreprocEntityDelta[list[GlobalTransform], list[GlobalTransform]] = (
            self.visit_node_transform(node_template.transform)
        )
        transform_before: Maybe[list[GlobalTransform]] = transform_delta.before
        transform_after: Maybe[list[GlobalTransform]] = transform_delta.after

        transformed_before_template = self._before_template
        if transform_before and not is_nothing(self._before_template):
            if _SCOPE_TRANSFORM_TEMPLATE_OUTCOME in self._before_cache:
                transformed_before_template = self._before_cache[_SCOPE_TRANSFORM_TEMPLATE_OUTCOME]
            else:
                for before_global_transform in transform_before:
                    if not is_nothing(before_global_transform.name):
                        transformed_before_template = self._apply_global_transform(
                            global_transform=before_global_transform,
                            parameters=self._before_parameters,
                            template=transformed_before_template,
                        )

                # Macro transformations won't remove the transform from the template
                if "Transform" in transformed_before_template:
                    transformed_before_template.pop("Transform")
                self._before_cache[_SCOPE_TRANSFORM_TEMPLATE_OUTCOME] = transformed_before_template

        transformed_after_template = self._after_template
        if transform_after and not is_nothing(self._after_template):
            transformed_after_template = self._after_template
            for after_global_transform in transform_after:
                if not is_nothing(after_global_transform.name):
                    transformed_after_template = self._apply_global_transform(
                        global_transform=after_global_transform,
                        parameters=self._after_parameters,
                        template=transformed_after_template,
                    )
            # Macro transformations won't remove the transform from the template
            if "Transform" in transformed_after_template:
                transformed_after_template.pop("Transform")
            self._after_cache[_SCOPE_TRANSFORM_TEMPLATE_OUTCOME] = transformed_after_template

        return transformed_before_template, transformed_after_template
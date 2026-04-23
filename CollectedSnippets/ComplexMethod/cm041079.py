def visit_node_transform(
        self, node_transform: NodeTransform
    ) -> PreprocEntityDelta[list[GlobalTransform], list[GlobalTransform]]:
        change_type = node_transform.change_type
        before = [] if change_type != ChangeType.CREATED else Nothing
        after = [] if change_type != ChangeType.REMOVED else Nothing
        for change_set_entity in node_transform.global_transforms:
            if not isinstance(change_set_entity.name.value, str):
                raise ValidationError("Key Name of transform definition must be a string.")

            delta: PreprocEntityDelta[GlobalTransform, GlobalTransform] = self.visit(
                change_set_entity=change_set_entity
            )
            delta_before = delta.before
            delta_after = delta.after
            if not is_nothing(before) and not is_nothing(delta_before):
                before.append(delta_before)
            if not is_nothing(after) and not is_nothing(delta_after):
                after.append(delta_after)
        return PreprocEntityDelta(before=before, after=after)
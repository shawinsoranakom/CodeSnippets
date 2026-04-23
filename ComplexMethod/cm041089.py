def visit_node_output(
        self, node_output: NodeOutput
    ) -> PreprocEntityDelta[PreprocOutput, PreprocOutput]:
        change_type = node_output.change_type
        value_delta = self.visit(node_output.value)

        condition_delta = Nothing
        if not is_nothing(node_output.condition_reference):
            condition_delta = self._resolve_resource_condition_reference(
                node_output.condition_reference
            )
            condition_before = condition_delta.before
            condition_after = condition_delta.after
            if not condition_before and condition_after:
                change_type = ChangeType.CREATED
            elif condition_before and not condition_after:
                change_type = ChangeType.REMOVED

        export_delta = Nothing
        if not is_nothing(node_output.export):
            export_delta = self.visit(node_output.export)

        before: Maybe[PreprocOutput] = Nothing
        if change_type != ChangeType.CREATED:
            before = PreprocOutput(
                name=node_output.name,
                value=value_delta.before,
                export=export_delta.before if export_delta else None,
                condition=condition_delta.before if condition_delta else None,
            )
        after: Maybe[PreprocOutput] = Nothing
        if change_type != ChangeType.REMOVED:
            after = PreprocOutput(
                name=node_output.name,
                value=value_delta.after,
                export=export_delta.after if export_delta else None,
                condition=condition_delta.after if condition_delta else None,
            )
        return PreprocEntityDelta(before=before, after=after)
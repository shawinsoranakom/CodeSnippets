def visit_node_array(self, node_array: NodeArray) -> PreprocEntityDelta:
        node_change_type = node_array.change_type
        before = [] if node_change_type != ChangeType.CREATED else Nothing
        after = [] if node_change_type != ChangeType.REMOVED else Nothing
        for change_set_entity in node_array.array:
            delta: PreprocEntityDelta = self.visit(change_set_entity=change_set_entity)
            delta_before = delta.before
            delta_after = delta.after
            if not is_nothing(before) and not is_nothing(delta_before):
                before.append(delta_before)
            if not is_nothing(after) and not is_nothing(delta_after):
                after.append(delta_after)
        return PreprocEntityDelta(before=before, after=after)
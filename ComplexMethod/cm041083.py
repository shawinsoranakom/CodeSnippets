def visit_node_object(self, node_object: NodeObject) -> PreprocEntityDelta:
        node_change_type = node_object.change_type
        before = {} if node_change_type != ChangeType.CREATED else Nothing
        after = {} if node_change_type != ChangeType.REMOVED else Nothing
        for name, change_set_entity in node_object.bindings.items():
            delta: PreprocEntityDelta = self.visit(change_set_entity=change_set_entity)
            delta_before = delta.before
            delta_after = delta.after
            if not is_nothing(before) and not is_nothing(delta_before):
                before[name] = delta_before
            if not is_nothing(after) and not is_nothing(delta_after):
                after[name] = delta_after
        return PreprocEntityDelta(before=before, after=after)
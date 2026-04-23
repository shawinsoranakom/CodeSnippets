def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Replace a call of the form `module.Class.func(...)` by a call of the form `super().func(...)`
        if the `Class` being called is one of the bases."""
        if self.is_call_to_parent_class(updated_node):
            full_parent_class_name = get_full_attribute_name(updated_node.func.value)
            # Replace only if it's a base, or a few special rules
            if (
                full_parent_class_name in self.new_bases
                or (full_parent_class_name == "nn.Module" and "GradientCheckpointingLayer" in self.new_bases)
                or (
                    full_parent_class_name == "PreTrainedModel"
                    and any("PreTrainedModel" in base for base in self.new_bases)
                )
            ):
                # Replace `full_parent_class_name.func(...)` with `super().func(...)`
                attribute_node = updated_node.func.with_changes(value=cst.Call(func=cst.Name("super")))
                # Check if the first argument is 'self', and remove it
                new_args = (
                    updated_node.args[1:]
                    if len(updated_node.args) > 0 and m.matches(updated_node.args[0].value, m.Name("self"))
                    else updated_node.args
                )
                return updated_node.with_changes(func=attribute_node, args=new_args)
        return updated_node
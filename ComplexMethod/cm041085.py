def visit_node_intrinsic_function_fn_if(
        self, node_intrinsic_function: NodeIntrinsicFunction
    ) -> PreprocEntityDelta:
        # `if` needs to be short-circuiting i.e. if the condition is True we don't evaluate the
        # False branch. If the condition is False, we don't evaluate the True branch.
        if len(node_intrinsic_function.arguments.array) != 3:
            raise ValueError(
                f"Incorrectly constructed Fn::If usage, expected 3 arguments, found {len(node_intrinsic_function.arguments.array)}"
            )

        condition_delta = self.visit(node_intrinsic_function.arguments.array[0])
        if_delta = PreprocEntityDelta()
        if not is_nothing(condition_delta.before):
            node_condition = self._get_node_condition_if_exists(
                condition_name=condition_delta.before
            )
            if is_nothing(node_condition):
                # TODO: I don't think this is a possible state since for us to be evaluating the before state,
                #  we must have successfully deployed the stack and as such this case was not reached before
                raise ValidationError(
                    f"Template error: unresolved condition dependency {condition_delta.before} in Fn::If"
                )

            condition_value = self.visit(node_condition).before
            if condition_value:
                arg_delta = self.visit(node_intrinsic_function.arguments.array[1])
            else:
                arg_delta = self.visit(node_intrinsic_function.arguments.array[2])
            if_delta.before = arg_delta.before

        if not is_nothing(condition_delta.after):
            node_condition = self._get_node_condition_if_exists(
                condition_name=condition_delta.after
            )
            if is_nothing(node_condition):
                raise ValidationError(
                    f"Template error: unresolved condition dependency {condition_delta.after} in Fn::If"
                )

            condition_value = self.visit(node_condition).after
            if condition_value:
                arg_delta = self.visit(node_intrinsic_function.arguments.array[1])
            else:
                arg_delta = self.visit(node_intrinsic_function.arguments.array[2])
            if_delta.after = arg_delta.after

        return if_delta
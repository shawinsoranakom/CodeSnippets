def _get_operations_list(self, module_operation_counts):
        forward_operations = [
            op for op in module_operation_counts["operations_list"] if not op["is_bw"]
        ]
        backward_operations = [
            op
            for op in module_operation_counts["operations_list"]
            if op["is_bw"] and not op["is_activation_checkpointing"]
        ]
        checkpointing_operations = [
            op
            for op in module_operation_counts["operations_list"]
            if op["is_activation_checkpointing"]
        ]

        return forward_operations, backward_operations, checkpointing_operations
def generate_comm_debug_tracing_table(self, noise_level=3):
        """
        Generates detailed table displaying operations and collective tracing information
        on a module level. Amount of information is dependent on noise_level

        0. prints module-level collective counts
        1. prints dTensor operations not included in trivial operations, module information
        2. prints operations not included in trivial operations
        3. prints all operations
        """

        (
            include_DTensor_ops,
            include_module_data,
            include_ops,
            include_trivial_ops,
        ) = self._set_noise_parameters(noise_level)

        table = ""
        for fqn in self.advanced_module_tracker.module_helper_dict:
            # setting up indentations for table formatting
            indent = "  " * (
                2 * self.advanced_module_tracker.module_helper_dict[fqn]["depth"]
            )
            table += f"{indent}{fqn}\n"

            if include_module_data:
                if (
                    "module_type"
                    in self.advanced_module_tracker.module_helper_dict[fqn]
                ):
                    module_type = self.advanced_module_tracker.module_helper_dict[fqn][
                        "module_type"
                    ]
                    table += f"{indent}*module type: {module_type}\n"

                if "parameters" in self.advanced_module_tracker.module_helper_dict[fqn]:
                    table += f"{indent}*Parameter List\n"
                    for (
                        param_name,
                        placement,
                    ) in self.advanced_module_tracker.module_helper_dict[fqn][
                        "parameters"
                    ].items():
                        table += f"{indent} *{param_name}: {placement}\n"

            indent += "  "
            collective_indent = "  " * (
                2 * self.advanced_module_tracker.module_helper_dict[fqn]["depth"] + 2
            )
            operation_indent = "  " * (
                2 * self.advanced_module_tracker.module_helper_dict[fqn]["depth"] + 3
            )

            # separate the module's collective and operations by forward and backward
            forward_collectives = {}
            backward_collectives = {}
            if fqn in self.comm_module_counts:
                forward_collectives = self.comm_module_counts[fqn]["forward"]
                backward_collectives = self.comm_module_counts[fqn]["backward"]

            forward_operations = []
            backward_operations = []
            checkpointing_operations = []

            if include_DTensor_ops:
                if fqn in self.comm_module_operation_counts:
                    (
                        forward_operations,
                        backward_operations,
                        checkpointing_operations,
                    ) = self._get_operations_list(
                        self.comm_module_operation_counts[fqn]
                    )

            def add_tracing_information(table, collectives_dict, operation_list):
                """
                adds tracing information for module's forward or backward
                """
                for collective, count in collectives_dict.items():
                    table += (
                        f"\033[1;33m{collective_indent}*{collective}: {count}\033[0m\n"
                    )

                def add_operations(
                    table, operation, collective_indent, operation_indent
                ):
                    """
                    adds operation information to the table
                    """
                    table += f"\033[1;33m{collective_indent}**{operation_name}\033[0m\n"

                    if len(operation["input_shape"]):
                        operation_shape = operation["input_shape"]
                        operation_sharding = operation["input_sharding"]
                        operation_device_mesh = operation["device_mesh"]

                        table += f"\033[1;31m{operation_indent}shape: {operation_shape}\033[0m\n"
                        table += f"\033[1;31m{operation_indent}sharding: {operation_sharding}\033[0m\n"
                        table += f"\033[1;31m{operation_indent}device mesh: {operation_device_mesh}\033[0m\n"

                    return table

                for operation in operation_list:
                    operation_name = str(operation["name"])

                    # include all operations
                    if include_trivial_ops:
                        table = add_operations(
                            table, operation, collective_indent, operation_indent
                        )

                    # include all operations not in trivial operations
                    elif include_ops and operation_name not in trivial_ops:
                        table = add_operations(
                            table, operation, collective_indent, operation_indent
                        )

                    # only include dTensor operations not in trivial set
                    elif (
                        include_DTensor_ops
                        and (operation_name not in trivial_ops)
                        and len(operation["input_shape"])
                    ):
                        table = add_operations(
                            table, operation, collective_indent, operation_indent
                        )

                return table

            if len(forward_collectives) or len(forward_operations):
                table += f"{indent}FORWARD PASS\n"
                table = add_tracing_information(
                    table, forward_collectives, forward_operations
                )

            if len(backward_collectives) or len(backward_operations):
                table += f"{indent}BACKWARD PASS\n"
                table = add_tracing_information(
                    table, backward_collectives, backward_operations
                )

            if len(checkpointing_operations):
                table += f"{indent}ACTIVATION CHECKPOINTING\n"
                table = add_tracing_information(table, {}, checkpointing_operations)

        return table
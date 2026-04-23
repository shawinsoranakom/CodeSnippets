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
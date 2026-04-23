def add_json_information(json_dict, fqn):
            json_dict["fqn"] = fqn
            json_dict["module_type"] = ""
            json_dict["parameters"] = []
            json_dict["children"] = []
            json_dict["collectives_forward"] = []
            json_dict["collectives_backward"] = []
            json_dict["operations_forward"] = []
            json_dict["operations_backward"] = []

            # adds module layer type and parameters, and their sharding
            if (
                "module_type" in self.advanced_module_tracker.module_helper_dict[fqn]
                and include_module_data
            ):
                json_dict["module_type"] = (
                    self.advanced_module_tracker.module_helper_dict[fqn]["module_type"]
                )

                if "parameters" in self.advanced_module_tracker.module_helper_dict[fqn]:
                    for (
                        param_name,
                        placement,
                    ) in self.advanced_module_tracker.module_helper_dict[fqn][
                        "parameters"
                    ].items():
                        json_dict["parameters"].append((param_name, placement))

            # adds module collective information
            if fqn in self.comm_module_counts:
                for collective, count in self.comm_module_counts[fqn][
                    "forward"
                ].items():
                    json_dict["collectives_forward"].append((str(collective), count))

                for collective, count in self.comm_module_counts[fqn][
                    "backward"
                ].items():
                    json_dict["collectives_backward"].append((str(collective), count))

            # adds module operation information
            forward_operations = []
            backward_operations = []
            checkpointing_operations = []

            # only get operations if the minimum operation noise level is set to true
            if include_DTensor_ops:
                if fqn in self.comm_module_operation_counts:
                    (
                        forward_operations,
                        backward_operations,
                        checkpointing_operations,
                    ) = self._get_operations_list(
                        self.comm_module_operation_counts[fqn]
                    )

            # remove all operations who don't have DTensor inputs
            if not include_ops:
                forward_operations = [
                    op for op in forward_operations if len(op["input_sharding"])
                ]
                backward_operations = [
                    op for op in backward_operations if len(op["input_sharding"])
                ]
                checkpointing_operations = [
                    op for op in checkpointing_operations if len(op["input_sharding"])
                ]

            # remove all operations in trivial operations set
            if not include_trivial_ops:
                forward_operations = [
                    op
                    for op in forward_operations
                    if str(op["name"]) not in trivial_ops
                ]
                backward_operations = [
                    op
                    for op in backward_operations
                    if str(op["name"]) not in trivial_ops
                ]
                checkpointing_operations = [
                    op
                    for op in checkpointing_operations
                    if str(op["name"]) not in trivial_ops
                ]

            # converts operation information into string format for json.dumps()
            forward_operations = copy.deepcopy(forward_operations)
            for op in forward_operations:
                op["name"] = str(op["name"])

                for i in range(len(op["input_sharding"])):
                    op["input_sharding"][i] = str(op["input_sharding"][i])
                    op["input_shape"][i] = str(op["input_shape"][i])

            backward_operations = copy.deepcopy(backward_operations)
            for op in backward_operations:
                op["name"] = str(op["name"])

                for i in range(len(op["input_sharding"])):
                    op["input_sharding"][i] = str(op["input_sharding"][i])
                    op["input_shape"][i] = str(op["input_shape"][i])

            checkpointing_operations = copy.deepcopy(checkpointing_operations)
            for op in checkpointing_operations:
                op["name"] = str(op["name"])

                for i in range(len(op["input_sharding"])):
                    op["input_sharding"][i] = str(op["input_sharding"][i])
                    op["input_shape"][i] = str(op["input_shape"][i])

            json_dict["operations_forward"] = forward_operations
            json_dict["operations_backward"] = backward_operations
            json_dict["operations_checkpointing"] = checkpointing_operations

            if fqn not in self.advanced_module_tracker.parent_dict:
                return json_dict

            # recursively adds module's children
            for ele in self.advanced_module_tracker.parent_dict[fqn]:
                json_dict["children"].append(add_json_information({}, ele))

            return json_dict
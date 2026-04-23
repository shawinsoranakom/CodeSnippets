def has_value(node: Node, name: str):
                return (
                    (
                        name in node.input_default
                        and node.input_default[name] is not None
                        and str(node.input_default[name]).strip() != ""
                    )
                    or (name in input_fields and input_fields[name].default is not None)
                    or (
                        name in node_input_mask
                        and node_input_mask[name] is not None
                        and str(node_input_mask[name]).strip() != ""
                    )
                )
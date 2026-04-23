async def validate_prompt(prompt_id, prompt, partial_execution_list: Union[list[str], None]):
    outputs = set()
    for x in prompt:
        if 'class_type' not in prompt[x]:
            node_data = prompt[x]
            node_title = node_data.get('_meta', {}).get('title')
            error = {
                "type": "missing_node_type",
                "message": f"Node '{node_title or f'ID #{x}'}' has no class_type. The workflow may be corrupted or a custom node is missing.",
                "details": f"Node ID '#{x}'",
                "extra_info": {
                    "node_id": x,
                    "class_type": None,
                    "node_title": node_title
                }
            }
            return (False, error, [], {})

        class_type = prompt[x]['class_type']
        class_ = nodes.NODE_CLASS_MAPPINGS.get(class_type, None)
        if class_ is None:
            node_data = prompt[x]
            node_title = node_data.get('_meta', {}).get('title', class_type)
            error = {
                "type": "missing_node_type",
                "message": f"Node '{node_title}' not found. The custom node may not be installed.",
                "details": f"Node ID '#{x}'",
                "extra_info": {
                    "node_id": x,
                    "class_type": class_type,
                    "node_title": node_title
                }
            }
            return (False, error, [], {})

        if hasattr(class_, 'OUTPUT_NODE') and class_.OUTPUT_NODE is True:
            if partial_execution_list is None or x in partial_execution_list:
                outputs.add(x)

    if len(outputs) == 0:
        error = {
            "type": "prompt_no_outputs",
            "message": "Prompt has no outputs",
            "details": "",
            "extra_info": {}
        }
        return (False, error, [], {})

    good_outputs = set()
    errors = []
    node_errors = {}
    validated = {}
    for o in outputs:
        valid = False
        reasons = []
        try:
            m = await validate_inputs(prompt_id, prompt, o, validated)
            valid = m[0]
            reasons = m[1]
        except Exception as ex:
            typ, _, tb = sys.exc_info()
            valid = False
            exception_type = full_type_name(typ)
            reasons = [{
                "type": "exception_during_validation",
                "message": "Exception when validating node",
                "details": str(ex),
                "extra_info": {
                    "exception_type": exception_type,
                    "traceback": traceback.format_tb(tb)
                }
            }]
            validated[o] = (False, reasons, o)

        if valid is True:
            good_outputs.add(o)
        else:
            logging.error(f"Failed to validate prompt for output {o}:")
            if len(reasons) > 0:
                logging.error("* (prompt):")
                for reason in reasons:
                    logging.error(f"  - {reason['message']}: {reason['details']}")
            errors += [(o, reasons)]
            for node_id, result in validated.items():
                valid = result[0]
                reasons = result[1]
                # If a node upstream has errors, the nodes downstream will also
                # be reported as invalid, but there will be no errors attached.
                # So don't return those nodes as having errors in the response.
                if valid is not True and len(reasons) > 0:
                    if node_id not in node_errors:
                        class_type = prompt[node_id]['class_type']
                        node_errors[node_id] = {
                            "errors": reasons,
                            "dependent_outputs": [],
                            "class_type": class_type
                        }
                        logging.error(f"* {class_type} {node_id}:")
                        for reason in reasons:
                            logging.error(f"  - {reason['message']}: {reason['details']}")
                    node_errors[node_id]["dependent_outputs"].append(o)
            logging.error("Output will be ignored")

    if len(good_outputs) == 0:
        errors_list = []
        for o, errors in errors:
            for error in errors:
                errors_list.append(f"{error['message']}: {error['details']}")
        errors_list = "\n".join(errors_list)

        error = {
            "type": "prompt_outputs_failed_validation",
            "message": "Prompt outputs failed validation",
            "details": errors_list,
            "extra_info": {}
        }

        return (False, error, list(good_outputs), node_errors)

    return (True, None, list(good_outputs), node_errors)
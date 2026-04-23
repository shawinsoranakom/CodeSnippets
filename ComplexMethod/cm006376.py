def update_projects_components_with_latest_component_versions(project_data, all_types_dict):
    all_types_dict_flat = flatten_components_with_aliases(all_types_dict)

    node_changes_log = defaultdict(list)
    project_data_copy = deepcopy(project_data)

    for node in project_data_copy.get("nodes", []):
        node_data = node.get("data").get("node")
        node_type = node.get("data").get("type")

        if node_type in all_types_dict_flat:
            latest_node = all_types_dict_flat.get(node_type)
            latest_template = latest_node.get("template")
            node_data["template"]["code"] = deepcopy(latest_template["code"])

            # Sync field_order so the UI renders fields in the correct order
            latest_field_order = latest_node.get("field_order")
            if latest_field_order is not None:
                node_data["field_order"] = latest_field_order

            # skip components that are having dynamic values that need to be persisted for templates

            if node_type in SKIPPED_COMPONENTS:
                continue

            is_tool_or_agent = node_data.get("tool_mode", False) or node_data.get("key") in {
                "Agent",
                "LanguageModelComponent",
                "TypeConverterComponent",
            }
            has_tool_outputs = any(output.get("types") == ["Tool"] for output in node_data.get("outputs", []))
            if "outputs" in latest_node and not has_tool_outputs and not is_tool_or_agent:
                # Deep copy to avoid mutating the shared latest_node template across flows
                new_outputs = deepcopy(latest_node["outputs"])
                # Set selected output as the previous selected output with type migration support
                type_migrations = {
                    "Data": "JSON",
                    "DataFrame": "Table",
                }
                for output in new_outputs:
                    node_data_output = next(
                        (output_ for output_ in node_data["outputs"] if output_["name"] == output["name"]),
                        None,
                    )
                    if node_data_output:
                        old_selected = node_data_output.get("selected")
                        if old_selected:
                            # Old flows may use Data/DataFrame; map to JSON/Table for backward compatibility
                            migrated_selected = type_migrations.get(old_selected, old_selected)
                            if migrated_selected in output.get("types", []):
                                output["selected"] = migrated_selected
                node_data["outputs"] = new_outputs

            if node_data["template"]["_type"] != latest_template["_type"]:
                node_data["template"]["_type"] = latest_template["_type"]
                if node_type != "Prompt":
                    node_data["template"] = deepcopy(latest_template)
                else:
                    for key, value in latest_template.items():
                        if key not in node_data["template"]:
                            node_changes_log[node_type].append(
                                {
                                    "attr": key,
                                    "old_value": None,
                                    "new_value": value,
                                }
                            )
                            node_data["template"][key] = deepcopy(value)
                        elif isinstance(value, dict) and value.get("value"):
                            node_changes_log[node_type].append(
                                {
                                    "attr": key,
                                    "old_value": node_data["template"][key],
                                    "new_value": value,
                                }
                            )
                            node_data["template"][key]["value"] = value["value"]
                    for key in node_data["template"]:
                        if key not in latest_template:
                            node_data["template"][key]["input_types"] = DEFAULT_PROMPT_INTUT_TYPES
                node_changes_log[node_type].append(
                    {
                        "attr": "_type",
                        "old_value": node_data["template"]["_type"],
                        "new_value": latest_template["_type"],
                    }
                )
            else:
                for attr in NODE_FORMAT_ATTRIBUTES:
                    latest_attr_value = latest_node.get(attr)
                    current_attr_value = node_data.get(attr)

                    if (
                        attr in latest_node
                        # Check if it needs to be updated
                        and latest_attr_value != current_attr_value
                    ):
                        node_changes_log[node_type].append(
                            {
                                "attr": attr,
                                "old_value": current_attr_value,
                                "new_value": latest_attr_value,
                            }
                        )
                        node_data[attr] = deepcopy(latest_attr_value)

                for field_name, field_dict in latest_template.items():
                    if field_name not in node_data["template"]:
                        node_data["template"][field_name] = deepcopy(field_dict)
                        continue
                    # The idea here is to update some attributes of the field
                    to_check_attributes = FIELD_FORMAT_ATTRIBUTES
                    # Skip specific field attributes that should respect the starter project template values.
                    # Currently we skip 'advanced' so that a field marked as advanced in the component code
                    # will NOT overwrite the value specified in the starter project template. This preserves
                    # the intended UX configuration of the starter projects.
                    # SKIPPED_FIELD_ATTRIBUTES = {"advanced"}
                    # Iterate through the attributes we want to potentially update
                    for attr in to_check_attributes:
                        # Respect the template value by not updating if the attribute is in the skipped set
                        if attr in SKIPPED_FIELD_ATTRIBUTES:
                            continue
                        if (
                            attr in field_dict
                            and attr in node_data["template"].get(field_name)
                            # Check if it needs to be updated
                            and field_dict[attr] != node_data["template"][field_name][attr]
                        ):
                            node_changes_log[node_type].append(
                                {
                                    "attr": f"{field_name}.{attr}",
                                    "old_value": node_data["template"][field_name][attr],
                                    "new_value": field_dict[attr],
                                }
                            )
                            node_data["template"][field_name][attr] = deepcopy(field_dict[attr])
            # Remove fields that are not in the latest template
            if node_type != "Prompt":
                for field_name in list(node_data["template"].keys()):
                    is_tool_mode_and_field_is_tools_metadata = (
                        node_data.get("tool_mode", False) and field_name == "tools_metadata"
                    )
                    if field_name not in latest_template and not is_tool_mode_and_field_is_tools_metadata:
                        node_data["template"].pop(field_name)
    log_node_changes(node_changes_log)
    return project_data_copy
def _merge_openapi_specs(specs: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Merge a list of OpenAPI specs into a single specification.
    :param specs:  a list of OpenAPI specs loaded in a dictionary
    :return: the dictionary of a merged spec.
    """
    merged_spec = {}
    for idx, spec in enumerate(specs):
        if idx == 0:
            merged_spec = copy.deepcopy(spec)
        else:
            # Merge paths
            if "paths" in spec:
                merged_spec.setdefault("paths", {}).update(spec.get("paths", {}))

            # Merge components
            if "components" in spec:
                if "components" not in merged_spec:
                    merged_spec["components"] = {}
                for component_type, component_value in spec["components"].items():
                    if component_type not in merged_spec["components"]:
                        merged_spec["components"][component_type] = component_value
                    else:
                        merged_spec["components"][component_type].update(component_value)

    # Update the initial part of the spec, i.e., info and correct LocalStack version
    top_content = yaml.safe_load(spec_top_info)
    # Set the correct version
    top_content["info"]["version"] = version.version
    merged_spec.update(top_content)
    return merged_spec
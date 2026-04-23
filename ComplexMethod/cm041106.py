def apply_json_patch_safe(subject, patch_operations, in_place=True, return_list=False):
    """Apply JSONPatch operations, using some customizations for compatibility with API GW
    resources."""

    results = []
    patch_operations = (
        [patch_operations] if isinstance(patch_operations, dict) else patch_operations
    )
    for operation in patch_operations:
        try:
            # special case: for "replace" operations, assume "" as the default value
            if operation["op"] == "replace" and operation.get("value") is None:
                operation["value"] = ""

            if operation["op"] != "remove" and operation.get("value") is None:
                LOG.info('Missing "value" in JSONPatch operation for %s: %s', subject, operation)
                continue

            if operation["op"] == "add":
                path = operation["path"]
                target = subject.get(path.strip("/"))
                target = target or common.extract_from_jsonpointer_path(subject, path)
                if not isinstance(target, list):
                    # for `add` operation, if the target does not exist, set it to an empty dict (default behaviour)
                    # previous behaviour was an empty list. Revisit this if issues arise.
                    # TODO: we are assigning a value, even if not `in_place=True`
                    common.assign_to_path(subject, path, value={}, delimiter="/")

                target = common.extract_from_jsonpointer_path(subject, path)
                if isinstance(target, list) and not path.endswith("/-"):
                    # if "path" is an attribute name pointing to an array in "subject", and we're running
                    # an "add" operation, then we should use the standard-compliant notation "/path/-"
                    operation["path"] = f"{path}/-"

            if operation["op"] == "remove":
                path = operation["path"]
                common.assign_to_path(subject, path, value={}, delimiter="/")

            result = apply_patch(subject, [operation], in_place=in_place)
            if not in_place:
                subject = result
            results.append(result)
        except JsonPointerException:
            pass  # path cannot be found - ignore
        except Exception as e:
            if "non-existent object" in str(e):
                if operation["op"] == "replace":
                    # fall back to an ADD operation if the REPLACE fails
                    operation["op"] = "add"
                    result = apply_patch(subject, [operation], in_place=in_place)
                    results.append(result)
                    continue
                if operation["op"] == "remove" and isinstance(subject, dict):
                    result = subject.pop(operation["path"], None)
                    results.append(result)
                    continue
            raise
    if return_list:
        return results
    return (results or [subject])[-1]
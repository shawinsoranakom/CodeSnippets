def check_bc(existing_schemas):
    new_schema_dict = load_schemas_to_dict()
    version_map = process_version_map(torch._C._get_operator_version_map())
    is_bc = True
    broken_ops = []
    for existing_schema in existing_schemas:
        is_allow_list, trust_not_core_aten = allow_listed(existing_schema)
        if is_allow_list:
            if trust_not_core_aten or not is_core_aten_op(existing_schema):
                log.info("schema: %s found on allowlist, skipping", existing_schema)
                continue
            else:
                log.info(
                    "schema: %s found on allowlist, but is a core ATen op, checking BC. "
                    "NOTE: If you have removed an operator we will conservatively assume that "
                    "it is a core ATen op. If the operator you removed is not a core ATen op, "
                    "please specify that in the ALLOW_LIST entry (see comment block on top "
                    "of ALLOW_LIST more info)",
                    existing_schema,
                )
        if has_valid_upgraders(existing_schema, version_map):
            if not is_core_aten_op(existing_schema):
                log.info("schema: %s has valid upgrader, skipping", existing_schema)
                continue
            else:
                log.info(
                    "schema: %s has a valid upgrader, but is a core ATen op, checking BC"
                )
        log.debug("processing existing schema: %s", existing_schema)
        matching_new_schemas = new_schema_dict.get(existing_schema.name, [])
        found = False
        for matching_new_schema in matching_new_schemas:
            if matching_new_schema.is_backward_compatible_with(existing_schema):
                found = True
                break
        if not found:
            log.warning(
                "Can NOT find backward compatible schemas after changes "
                "for schema %s from the following candidates:\n[\n%s\n]",
                existing_schema,
                "\n\t".join(str(s) for s in matching_new_schemas),
            )
            # TODO Print out more details about why candidates don't match.
            broken_ops.append(str(existing_schema))
            is_bc = False
    if is_bc:
        log.info("Found backward compatible schemas for all existing schemas")
    else:
        log.warning(
            "The PR is introducing backward incompatible changes to the "
            "operator library. Please contact PyTorch team to confirm "
            "whether this change is wanted or not. \n\nBroken ops: "
            "[\n\t%s\n]",
            "\n\t".join(broken_ops),
        )
    return is_bc
def check_fc(existing_schemas):
    new_schema_dict = load_schemas_to_dict()
    is_fc = True
    broken_ops = []
    for existing_schema in existing_schemas:
        is_allow_list, _ = allow_listed(existing_schema)
        if is_allow_list:
            log.info("schema: %s found on allowlist, skipping", existing_schema)
            continue
        log.info("processing existing schema: %s", existing_schema)
        matching_new_schemas = new_schema_dict.get(existing_schema.name, [])
        found = False
        possible_failure_reasons = []
        for matching_new_schema in matching_new_schemas:
            is_compatible, reason = matching_new_schema.check_forward_compatible_with(
                existing_schema
            )
            if is_compatible:
                found = True
                break
            if reason != "":
                possible_failure_reasons.append(reason)
        if not found:
            log.warning(
                "Can NOT find forward compatible schemas after changes "
                "for schema %s from the following candidates:\n[\n\t%s\n]",
                existing_schema,
                "\n\t".join(str(s) for s in matching_new_schemas),
            )
            log.warning(
                "Refer to following reasons for failure to find FC schema:\n[\n%s\n]",
                "\n\t".join(str(r) for r in possible_failure_reasons),
            )
            broken_ops.append(str(existing_schema))
            is_fc = False
    if is_fc:
        log.info("Found forward compatible schemas for all existing schemas")
    else:
        log.warning(
            "The PR is introducing a potentially forward incompatible changes to the "
            "operator library. Please contact PyTorch team to confirm "
            "whether this change is wanted or not. \n\nBroken ops: "
            "[\n\t%s\n]",
            "\n\t".join(broken_ops),
        )
def get_attr_from_model_instance(
    resource: dict,
    attribute_name: str,
    resource_type: str,
    resource_id: str,
    attribute_sub_name: str | None = None,
) -> str:
    if resource["PhysicalResourceId"] == MOCK_REFERENCE:
        LOG.warning(
            "Attribute '%s' requested from unsupported resource with id %s",
            attribute_name,
            resource_id,
        )
        return MOCK_REFERENCE

    properties = resource.get("Properties", {})
    # if there's no entry in VALID_GETATT_PROPERTIES for the resource type we still default to "open" and accept anything
    valid_atts = VALID_GETATT_PROPERTIES.get(resource_type)
    if valid_atts is not None and attribute_name not in valid_atts:
        LOG.warning(
            "Invalid attribute in Fn::GetAtt for %s:  | %s.%s",
            resource_type,
            resource_id,
            attribute_name,
        )
        raise Exception(
            f"Resource type {resource_type} does not support attribute {{{attribute_name}}}"
        )  # TODO: check CFn behavior via snapshot

    attribute_candidate = properties.get(attribute_name)
    if attribute_sub_name:
        return attribute_candidate.get(attribute_sub_name)
    if "." in attribute_name:
        # was used for legacy, but keeping it since it might have to work for a custom resource as well
        if attribute_candidate:
            return attribute_candidate

        # some resources (e.g. ElastiCache) have their readOnly attributes defined as Aa.Bb but the property is named AaBb
        if attribute_candidate := properties.get(attribute_name.replace(".", "")):
            return attribute_candidate

        # accessing nested properties
        parts = attribute_name.split(".")
        attribute = properties
        # TODO: the attribute fetching below is a temporary workaround for the dependency resolution.
        #  It is caused by trying to access the resource attribute that has not been deployed yet.
        #  This should be a hard error.“
        for part in parts:
            if attribute is None:
                return None
            attribute = attribute.get(part)
        return attribute

    # If we couldn't find the attribute, this is actually an irrecoverable error.
    # After the resource has a state of CREATE_COMPLETE, all attributes should already be set.
    # TODO: raise here instead
    # if attribute_candidate is None:
    # raise Exception(
    #     f"Failed to resolve attribute for Fn::GetAtt in {resource_type}: {resource_id}.{attribute_name}"
    # )  # TODO: check CFn behavior via snapshot
    return attribute_candidate
def async_discover_entities(
    endpoint: MatterEndpoint,
) -> Generator[MatterEntityInfo]:
    """Run discovery on MatterEndpoint and return matching MatterEntityInfo(s)."""
    discovered_attributes: set[type[ClusterAttributeDescriptor]] = set()
    device_info = endpoint.device_info
    for schema in iter_schemas():
        # abort if attribute(s) already discovered
        if any(x in schema.required_attributes for x in discovered_attributes):
            continue

        primary_attribute = schema.required_attributes[0]

        # check vendor_id
        if (
            schema.vendor_id is not None
            and device_info.vendorID not in schema.vendor_id
        ):
            continue

        # check product_id
        if (
            schema.product_id is not None
            and device_info.productID not in schema.product_id
        ):
            continue

        # check product_name
        if (
            schema.product_name is not None
            and device_info.productName not in schema.product_name
        ):
            continue

        # check required device_type
        if schema.device_type is not None and not any(
            x in schema.device_type for x in endpoint.device_types
        ):
            continue

        # check absent device_type
        if schema.not_device_type is not None and any(
            x in schema.not_device_type for x in endpoint.device_types
        ):
            continue

        # check endpoint_id
        if (
            schema.endpoint_id is not None
            and endpoint.endpoint_id not in schema.endpoint_id
        ):
            continue

        # check required attributes
        if schema.required_attributes is not None and not all(
            endpoint.has_attribute(None, val_schema)
            for val_schema in schema.required_attributes
        ):
            continue

        # check for endpoint-attributes that may not be present
        if schema.absent_attributes is not None and any(
            endpoint.has_attribute(None, val_schema)
            for val_schema in schema.absent_attributes
        ):
            continue

        # check for clusters that may not be present
        if schema.absent_clusters is not None and any(
            endpoint.node.has_cluster(val_schema)
            for val_schema in schema.absent_clusters
        ):
            continue

        # check for required value in cluster featuremap
        if schema.featuremap_contains is not None and (
            not bool(
                int(
                    endpoint.get_attribute_value(
                        primary_attribute.cluster_id, FEATUREMAP_ATTRIBUTE_ID
                    )
                )
                & schema.featuremap_contains
            )
        ):
            continue

        # BEGIN checks on actual attribute values
        # these are the least likely to be used and least efficient, so they are checked last

        # check if PRIMARY value exists but is none/null
        if not schema.allow_none_value and any(
            endpoint.get_attribute_value(None, val_schema) in (None, NullValue)
            for val_schema in schema.required_attributes
        ):
            continue

        # check for required value in PRIMARY attribute
        primary_value = endpoint.get_attribute_value(None, primary_attribute)
        if schema.value_contains is not UNSET and (
            isinstance(primary_value, list)
            and schema.value_contains not in primary_value
        ):
            continue

        # check for value that may not be present in PRIMARY attribute
        if schema.value_is_not is not UNSET and (
            schema.value_is_not == primary_value
            or (
                isinstance(primary_value, list) and schema.value_is_not in primary_value
            )
        ):
            continue

        # check for value that may not be present in SECONDARY attribute
        secondary_attribute = (
            schema.required_attributes[1]
            if len(schema.required_attributes) > 1
            else None
        )
        secondary_value = (
            endpoint.get_attribute_value(None, secondary_attribute)
            if secondary_attribute
            else None
        )
        if schema.secondary_value_is_not is not UNSET and (
            (schema.secondary_value_is_not == secondary_value)
            or (
                isinstance(secondary_value, list)
                and schema.secondary_value_is_not in secondary_value
            )
        ):
            continue

        # check for required value in SECONDARY attribute
        if schema.secondary_value_contains is not UNSET and (
            isinstance(secondary_value, list)
            and schema.secondary_value_contains not in secondary_value
        ):
            continue

        # FINISH all validation checks
        # all checks passed, this value belongs to an entity

        attributes_to_watch = list(schema.required_attributes)
        if schema.optional_attributes:
            # check optional attributes
            for optional_attribute in schema.optional_attributes:
                if optional_attribute in attributes_to_watch:
                    continue
                if endpoint.has_attribute(None, optional_attribute):
                    attributes_to_watch.append(optional_attribute)

        yield MatterEntityInfo(
            endpoint=endpoint,
            platform=schema.platform,
            attributes_to_watch=attributes_to_watch,
            entity_description=schema.entity_description,
            entity_class=schema.entity_class,
            discovery_schema=schema,
        )

        # prevent re-discovery of the primary attribute if not allowed
        if not schema.allow_multi:
            discovered_attributes.update(schema.required_attributes)
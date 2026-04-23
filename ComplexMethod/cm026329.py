def get_light_attribute_sets(
    node: HomeeNode,
) -> list[dict[AttributeType, HomeeAttribute]]:
    """Return the lights with their attributes as found in the node."""
    lights: list[dict[AttributeType, HomeeAttribute]] = []
    on_off_attributes = [
        i for i in node.attributes if i.type == AttributeType.ON_OFF and i.editable
    ]
    for a in on_off_attributes:
        attribute_dict: dict[AttributeType, HomeeAttribute] = {a.type: a}
        for attribute in node.attributes:
            if attribute.instance == a.instance and attribute.type in LIGHT_ATTRIBUTES:
                attribute_dict[attribute.type] = attribute
        lights.append(attribute_dict)

    return lights
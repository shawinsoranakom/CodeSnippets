def marshall(
    pydeck_proto: PydeckProto,
    pydeck_obj: Optional["Deck"],
    use_container_width: bool,
) -> None:
    if pydeck_obj is None:
        spec = json.dumps(EMPTY_MAP)
    else:
        spec = pydeck_obj.to_json()

    pydeck_proto.json = spec
    pydeck_proto.use_container_width = use_container_width

    tooltip = _get_pydeck_tooltip(pydeck_obj)
    if tooltip:
        pydeck_proto.tooltip = json.dumps(tooltip)
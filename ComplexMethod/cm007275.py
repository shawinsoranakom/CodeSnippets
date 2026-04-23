def get_component_type_aliases(
    component_name: str,
    component_data: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    """Return the known aliases for a component type."""
    aliases: list[str] = [component_name]
    aliases.extend(old_name for old_name, new_name in LEGACY_TYPE_ALIASES.items() if new_name == component_name)

    if component_data:
        for field_name in ("name", "display_name"):
            value = component_data.get(field_name)
            if isinstance(value, str) and value:
                aliases.append(value)

        template = component_data.get("template")
        if isinstance(template, Mapping):
            component_class_name = template.get("_type")
            if (
                isinstance(component_class_name, str)
                and component_class_name
                and component_class_name.endswith("Component")
            ):
                aliases.append(component_class_name.removesuffix("Component"))

    deduped_aliases = dict.fromkeys(alias for alias in aliases if alias)
    return tuple(deduped_aliases)
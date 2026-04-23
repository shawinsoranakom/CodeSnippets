def process_status(status: dict[str, ComponentStatus]) -> dict[str, ComponentStatus]:
    """Remove disabled capabilities from status."""
    if (main_component := status.get(MAIN)) is None:
        return status
    if (
        disabled_components_capability := main_component.get(
            Capability.CUSTOM_DISABLED_COMPONENTS
        )
    ) is not None:
        disabled_components = cast(
            list[str],
            disabled_components_capability[Attribute.DISABLED_COMPONENTS].value,
        )
        if disabled_components is not None:
            for component in disabled_components:
                # Burner components are named burner-06
                # but disabledComponents contain burner-6
                if "burner" in component:
                    burner_id = int(component.split("-")[-1])
                    component = f"burner-0{burner_id}"
                # Don't delete 'lamp' component even when disabled
                if component in status and component != "lamp":
                    del status[component]
    for component_status in status.values():
        process_component_status(component_status)
    return status
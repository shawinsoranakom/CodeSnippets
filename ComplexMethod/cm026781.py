def _migrate_to_new_unique_id(
    hass: HomeAssistant, model: str, serial_number: str
) -> None:
    """Migrate old unique ids to new unique ids."""
    ent_reg = er.async_get(hass)
    name_list = [
        "Voltage",
        "Current",
        "Power",
        "ImportEnergy",
        "ExportGrid",
        "Frequency",
        "PF",
    ]
    phase_list = ["A", "B", "C", "NET"]
    id_phase_range = 1 if model == DEVICE_3080 else 4
    id_name_range = 5 if model == DEVICE_3080 else 7
    for row in range(id_phase_range):
        for idx in range(id_name_range):
            old_unique_id = f"{serial_number}-{row}-{idx}"
            new_unique_id = (
                f"{serial_number}_{name_list[idx]}"
                if model == DEVICE_3080
                else f"{serial_number}_{name_list[idx]}_{phase_list[row]}"
            )
            entity_id = ent_reg.async_get_entity_id(
                Platform.SENSOR, DOMAIN, old_unique_id
            )
            if entity_id is not None:
                try:
                    ent_reg.async_update_entity(entity_id, new_unique_id=new_unique_id)
                except ValueError:
                    _LOGGER.warning(
                        "Skip migration of id [%s] to [%s] because it already exists",
                        old_unique_id,
                        new_unique_id,
                    )
                else:
                    _LOGGER.debug(
                        "Migrating unique_id from [%s] to [%s]",
                        old_unique_id,
                        new_unique_id,
                    )
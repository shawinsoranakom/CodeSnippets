async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: RoborockConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Roborock button platform."""
    routines_lists = await asyncio.gather(
        *[coordinator.get_routines() for coordinator in config_entry.runtime_data.v1],
    )
    async_add_entities(
        itertools.chain(
            (
                RoborockButtonEntity(
                    coordinator,
                    description,
                )
                for coordinator in config_entry.runtime_data.v1
                for description in CONSUMABLE_BUTTON_DESCRIPTIONS
                if isinstance(coordinator, RoborockDataUpdateCoordinator)
            ),
            (
                RoborockRoutineButtonEntity(
                    coordinator,
                    ButtonEntityDescription(
                        key=str(routine.id),
                        name=routine.name,
                    ),
                )
                for coordinator, routines in zip(
                    config_entry.runtime_data.v1, routines_lists, strict=True
                )
                for routine in routines
            ),
            (
                RoborockButtonEntityA01(
                    coordinator,
                    description,
                )
                for coordinator in config_entry.runtime_data.a01
                if isinstance(coordinator, RoborockWashingMachineUpdateCoordinator)
                for description in ZEO_BUTTON_DESCRIPTIONS
            ),
            (
                RoborockQ10EmptyDustbinButtonEntity(
                    coordinator,
                    description,
                )
                for coordinator in config_entry.runtime_data.b01_q10
                for description in Q10_BUTTON_DESCRIPTIONS
            ),
        )
    )
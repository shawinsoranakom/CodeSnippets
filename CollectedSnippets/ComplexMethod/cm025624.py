async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: EnphaseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up envoy sensor platform."""
    coordinator = config_entry.runtime_data
    envoy_data = coordinator.envoy.data
    assert envoy_data is not None
    _LOGGER.debug("Envoy data: %s", envoy_data)

    entities: list[Entity] = [
        EnvoyProductionEntity(coordinator, description)
        for description in PRODUCTION_SENSORS
    ]
    if envoy_data.system_consumption:
        entities.extend(
            EnvoyConsumptionEntity(coordinator, description)
            for description in CONSUMPTION_SENSORS
        )
    if envoy_data.system_net_consumption:
        entities.extend(
            EnvoyNetConsumptionEntity(coordinator, description)
            for description in NET_CONSUMPTION_SENSORS
        )
    # For each production phase reported add production entities
    if envoy_data.system_production_phases:
        entities.extend(
            EnvoyProductionPhaseEntity(coordinator, description)
            for use_phase, phase in envoy_data.system_production_phases.items()
            for description in PRODUCTION_PHASE_SENSORS[use_phase]
            if phase is not None
        )
    # For each consumption phase reported add consumption entities
    if envoy_data.system_consumption_phases:
        entities.extend(
            EnvoyConsumptionPhaseEntity(coordinator, description)
            for use_phase, phase in envoy_data.system_consumption_phases.items()
            for description in CONSUMPTION_PHASE_SENSORS[use_phase]
            if phase is not None
        )
    # For each net_consumption phase reported add consumption entities
    if envoy_data.system_net_consumption_phases:
        entities.extend(
            EnvoyNetConsumptionPhaseEntity(coordinator, description)
            for use_phase, phase in envoy_data.system_net_consumption_phases.items()
            for description in NET_CONSUMPTION_PHASE_SENSORS[use_phase]
            if phase is not None
        )
    # Add Current Transformer entities
    if envoy_data.ctmeters:
        entities.extend(
            EnvoyCTEntity(coordinator, description)
            for description in CT_SENSORS
            if description.cttype in envoy_data.ctmeters
        )
    # Add Current Transformer phase entities
    if ctmeters_phases := envoy_data.ctmeters_phases:
        entities.extend(
            EnvoyCTPhaseEntity(coordinator, description)
            for phase, descriptions in CT_PHASE_SENSORS.items()
            for description in descriptions
            if (cttype := description.cttype) in ctmeters_phases
            and phase in ctmeters_phases[cttype]
        )

    if envoy_data.inverters:
        entities.extend(
            EnvoyInverterEntity(coordinator, description, inverter)
            for description in INVERTER_SENSORS
            for inverter in envoy_data.inverters
        )

    if envoy_data.encharge_inventory:
        entities.extend(
            EnvoyEnchargeInventoryEntity(coordinator, description, encharge)
            for description in ENCHARGE_INVENTORY_SENSORS
            for encharge in envoy_data.encharge_inventory
        )
    if envoy_data.encharge_power:
        entities.extend(
            EnvoyEnchargePowerEntity(coordinator, description, encharge)
            for description in ENCHARGE_POWER_SENSORS
            for encharge in envoy_data.encharge_power
        )
    if envoy_data.encharge_aggregate:
        entities.extend(
            EnvoyEnchargeAggregateEntity(coordinator, description)
            for description in ENCHARGE_AGGREGATE_SENSORS
        )
    if envoy_data.enpower:
        entities.extend(
            EnvoyEnpowerEntity(coordinator, description)
            for description in ENPOWER_SENSORS
        )
    if envoy_data.acb_power:
        entities.extend(
            EnvoyAcbBatteryPowerEntity(coordinator, description)
            for description in ACB_BATTERY_POWER_SENSORS
        )
        entities.extend(
            EnvoyAcbBatteryEnergyEntity(coordinator, description)
            for description in ACB_BATTERY_ENERGY_SENSORS
        )
    if envoy_data.battery_aggregate:
        entities.extend(
            AggregateBatteryEntity(coordinator, description)
            for description in AGGREGATE_BATTERY_SENSORS
        )
    if envoy_data.collar:
        entities.extend(
            EnvoyCollarEntity(coordinator, description)
            for description in COLLAR_SENSORS
        )
    if envoy_data.c6cc:
        entities.extend(
            EnvoyC6CCEntity(coordinator, description) for description in C6CC_SENSORS
        )

    async_add_entities(entities)
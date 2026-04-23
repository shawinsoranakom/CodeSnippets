def _add_new_zones(zones: Iterable[tuple[Zone, Controller]]) -> None:
        async_add_entities(
            [
                HydrawiseSensor(
                    coordinators.water_use, description, controller, zone_id=zone.id
                )
                for zone, controller in zones
                for description in WATER_USE_ZONE_SENSORS
            ]
            + [
                HydrawiseSensor(
                    coordinators.main, description, controller, zone_id=zone.id
                )
                for zone, controller in zones
                for description in ZONE_SENSORS
            ]
            + [
                HydrawiseSensor(
                    coordinators.water_use,
                    description,
                    controller,
                    zone_id=zone.id,
                )
                for zone, controller in zones
                for description in FLOW_ZONE_SENSORS
                if _has_flow_sensor(controller)
            ]
        )
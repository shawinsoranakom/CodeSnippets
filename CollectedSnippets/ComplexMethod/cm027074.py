def _async_add_new_devices(mower_ids: set[str]) -> None:
        async_add_entities(
            AutomowerScheduleSwitchEntity(mower_id, coordinator)
            for mower_id in mower_ids
        )
        for mower_id in mower_ids:
            mower_data = coordinator.data[mower_id]
            if (
                mower_data.capabilities.stay_out_zones
                and mower_data.stay_out_zones is not None
                and mower_data.stay_out_zones.zones is not None
            ):
                _async_add_new_stay_out_zones(
                    mower_id, set(mower_data.stay_out_zones.zones.keys())
                )
            if mower_data.capabilities.work_areas and mower_data.work_areas is not None:
                _async_add_new_work_areas(mower_id, set(mower_data.work_areas.keys()))
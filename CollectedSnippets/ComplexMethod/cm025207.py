def update_groups():
        """Update the groups objects with the latest info from the bridge."""
        lights_changed = update_lights()

        try:
            bridge.update_scene_list(config[CONF_INTERVAL_LIGHTIFY_CONF])
            new_groups = bridge.update_group_list(config[CONF_INTERVAL_LIGHTIFY_CONF])
            groups_updated = bridge.groups_updated()
        except TimeoutError:
            _LOGGER.error("Timeout during updating of scenes/groups")
            return 0
        except OSError:
            _LOGGER.error("OSError during updating of scenes/groups")
            return 0

        if new_groups:
            new_groups = {group.idx(): group for group in new_groups.values()}
            new_entities = []
            for idx, group in new_groups.items():
                if idx not in groups:
                    osram_group = OsramLightifyGroup(
                        group, update_groups, groups_updated
                    )
                    groups[idx] = osram_group
                    new_entities.append(osram_group)
                else:
                    groups[idx].update_luminary(group)

            add_entities(new_entities)

        if groups_updated > groups_last_updated[0]:
            groups_last_updated[0] = groups_updated
            for idx, osram_group in groups.items():
                if idx not in new_groups:
                    osram_group.update_static_attributes()

        return max(lights_changed, groups_updated)
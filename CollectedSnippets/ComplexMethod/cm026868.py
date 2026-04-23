def _categorize_programs(isy_data: IsyData, programs: Programs) -> None:
    """Categorize the ISY programs."""
    for platform in PROGRAM_PLATFORMS:
        folder = programs.get_by_name(f"{DEFAULT_PROGRAM_STRING}{platform}")
        if not folder:
            continue

        for dtype, _, node_id in folder.children:
            if dtype != TAG_FOLDER:
                continue
            entity_folder: Programs = folder[node_id]
            actions = None
            status = entity_folder.get_by_name(KEY_STATUS)
            if not status or status.protocol != PROTO_PROGRAM:
                _LOGGER.warning(
                    "Program %s entity '%s' not loaded, invalid/missing status program",
                    platform,
                    entity_folder.name,
                )
                continue

            if platform != Platform.BINARY_SENSOR:
                actions = entity_folder.get_by_name(KEY_ACTIONS)
                if not actions or actions.protocol != PROTO_PROGRAM:
                    _LOGGER.warning(
                        (
                            "Program %s entity '%s' not loaded, invalid/missing actions"
                            " program"
                        ),
                        platform,
                        entity_folder.name,
                    )
                    continue

            entity = (entity_folder.name, status, actions)
            isy_data.programs[platform].append(entity)
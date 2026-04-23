async def _async_migrate_func(
        self, old_major_version: int, old_minor_version: int, old_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Migrate to the new version."""
        if old_major_version == 1:
            data = old_data
            if old_minor_version < 2:
                # Deduplicate datasets
                datasets: dict[str, DatasetEntry] = {}
                preferred_dataset = old_data["preferred_dataset"]

                for dataset in old_data["datasets"]:
                    created = cast(datetime, dt_util.parse_datetime(dataset["created"]))
                    entry = DatasetEntry(
                        created=created,
                        id=dataset["id"],
                        preferred_border_agent_id=None,
                        preferred_extended_address=None,
                        source=dataset["source"],
                        tlv=dataset["tlv"],
                    )
                    if (
                        MeshcopTLVType.EXTPANID not in entry.dataset
                        or MeshcopTLVType.ACTIVETIMESTAMP not in entry.dataset
                    ):
                        _LOGGER.warning(
                            "Dropped invalid Thread dataset:\n%s",
                            pformat(_format_dataset(entry.dataset)),
                        )
                        if entry.id == preferred_dataset:
                            preferred_dataset = None
                        continue

                    if entry.extended_pan_id in datasets:
                        if datasets[entry.extended_pan_id].id == preferred_dataset:
                            _LOGGER.warning(
                                "Dropped duplicated Thread dataset"
                                " (duplicate of preferred dataset):\n%s\nkept:\n%s",
                                pformat(_format_dataset(entry.dataset)),
                                pformat(
                                    _format_dataset(
                                        datasets[entry.extended_pan_id].dataset
                                    )
                                ),
                            )
                            continue
                        new_timestamp = cast(
                            tlv_parser.Timestamp,
                            entry.dataset[MeshcopTLVType.ACTIVETIMESTAMP],
                        )
                        old_timestamp = cast(
                            tlv_parser.Timestamp,
                            datasets[entry.extended_pan_id].dataset[
                                MeshcopTLVType.ACTIVETIMESTAMP
                            ],
                        )
                        if (old_timestamp.seconds, old_timestamp.ticks) >= (
                            new_timestamp.seconds,
                            new_timestamp.ticks,
                        ):
                            _LOGGER.warning(
                                "Dropped duplicated Thread dataset:\n%s\nkept:\n%s",
                                pformat(_format_dataset(entry.dataset)),
                                pformat(
                                    _format_dataset(
                                        datasets[entry.extended_pan_id].dataset
                                    )
                                ),
                            )
                            continue
                        _LOGGER.warning(
                            "Dropped duplicated Thread dataset:\n%s\nkept:\n%s",
                            pformat(
                                _format_dataset(datasets[entry.extended_pan_id].dataset)
                            ),
                            pformat(_format_dataset(entry.dataset)),
                        )
                    datasets[entry.extended_pan_id] = entry
                data = {
                    "preferred_dataset": preferred_dataset,
                    "datasets": [dataset.to_json() for dataset in datasets.values()],
                }
            # Migration to version 1.3 removed, it added the ID of the preferred border
            # agent
            if old_minor_version < 4:
                # Add extended address of the preferred border agent and clear border
                # agent ID
                for dataset in data["datasets"]:
                    dataset["preferred_border_agent_id"] = None
                    dataset["preferred_extended_address"] = None

        return data
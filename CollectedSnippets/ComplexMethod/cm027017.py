def async_add(
        self,
        source: str,
        tlv: str,
        preferred_border_agent_id: str | None,
        preferred_extended_address: str | None,
    ) -> None:
        """Add dataset, does nothing if it already exists."""
        # Make sure the tlv is valid
        dataset = tlv_parser.parse_tlv(tlv)

        # Don't allow adding a dataset which does not have an extended pan id or
        # timestamp
        if (
            MeshcopTLVType.EXTPANID not in dataset
            or MeshcopTLVType.ACTIVETIMESTAMP not in dataset
        ):
            raise HomeAssistantError("Invalid dataset")

        # Don't allow setting preferred border agent ID without setting
        # preferred extended address
        if preferred_border_agent_id is not None and preferred_extended_address is None:
            raise HomeAssistantError(
                "Must set preferred extended address with preferred border agent ID"
            )

        # Bail out if the dataset already exists
        entry: DatasetEntry | None
        for entry in self.datasets.values():
            if entry.dataset == dataset:
                if (
                    preferred_extended_address
                    and entry.preferred_extended_address is None
                ):
                    self.async_set_preferred_border_agent(
                        entry.id, preferred_border_agent_id, preferred_extended_address
                    )
                return

        # Update if dataset with same extended pan id exists and the timestamp
        # is newer
        if entry := next(
            (
                entry
                for entry in self.datasets.values()
                if entry.dataset[MeshcopTLVType.EXTPANID]
                == dataset[MeshcopTLVType.EXTPANID]
            ),
            None,
        ):
            new_timestamp = cast(
                tlv_parser.Timestamp, dataset[MeshcopTLVType.ACTIVETIMESTAMP]
            )
            old_timestamp = cast(
                tlv_parser.Timestamp,
                entry.dataset[MeshcopTLVType.ACTIVETIMESTAMP],
            )
            old_ts = (old_timestamp.seconds, old_timestamp.ticks)
            new_ts = (new_timestamp.seconds, new_timestamp.ticks)
            if old_ts >= new_ts:
                # Silently accept if the only addition is WAKEUP_CHANNEL:
                # it was added in OpenThread but the wake-up protocol isn't
                # defined yet, so we treat it as if it were always present.
                dataset_without_wakeup = {
                    k: v
                    for k, v in dataset.items()
                    if k != MeshcopTLVType.WAKEUP_CHANNEL
                }
                if old_ts > new_ts or dataset_without_wakeup != entry.dataset:
                    _LOGGER.warning(
                        "Got dataset with same extended PAN ID and same or older"
                        " active timestamp\nold:\n%s\nnew:\n%s",
                        pformat(_format_dataset(entry.dataset)),
                        pformat(_format_dataset(dataset)),
                    )
                    return
            elif _LOGGER.isEnabledFor(logging.DEBUG):
                _LOGGER.debug(
                    "Updating dataset with same extended PAN ID and newer"
                    " active timestamp\nold:\n%s\nnew:\n%s",
                    pformat(_format_dataset(entry.dataset)),
                    pformat(_format_dataset(dataset)),
                )
            self.datasets[entry.id] = dataclasses.replace(
                self.datasets[entry.id], tlv=tlv
            )
            self.async_schedule_save()
            if preferred_extended_address and entry.preferred_extended_address is None:
                self.async_set_preferred_border_agent(
                    entry.id, preferred_border_agent_id, preferred_extended_address
                )
            return

        entry = DatasetEntry(
            preferred_border_agent_id=preferred_border_agent_id,
            preferred_extended_address=preferred_extended_address,
            source=source,
            tlv=tlv,
        )
        self.datasets[entry.id] = entry
        self.async_schedule_save()

        # Set the new network as preferred if there is no preferred dataset and there is
        # no other router present. We only attempt this once.
        if (
            self._preferred_dataset is None
            and preferred_extended_address
            and not self._set_preferred_dataset_task
        ):
            self._set_preferred_dataset_task = self.hass.async_create_task(
                self._set_preferred_dataset_if_only_network(
                    entry.id, preferred_extended_address
                )
            )
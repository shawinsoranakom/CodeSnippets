def _async_update_ibeacon_with_unique_address(
        self,
        group_id: str,
        service_info: bluetooth.BluetoothServiceInfoBleak,
        ibeacon_advertisement: iBeaconAdvertisement,
    ) -> None:
        # Handle iBeacon with a fixed mac address
        # and or detect if the iBeacon is using a rotating mac address
        # and switch to random mac tracking method
        address = service_info.address
        unique_id = f"{group_id}_{address}"
        new = unique_id not in self._last_ibeacon_advertisement_by_unique_id
        uuid = str(ibeacon_advertisement.uuid)

        # Reject creating new trackers if the name is not set (unless the uuid is allowlisted).
        if (
            new
            and uuid not in self._allow_nameless_uuids
            and (
                service_info.device.name is None
                or service_info.device.name.replace("-", ":")
                == service_info.device.address
            )
        ):
            # Store the ignored addresses, cause the uuid might be allowlisted later
            self._ignored_nameless_by_uuid.setdefault(uuid, set()).add(address)

            _LOGGER.debug("ignoring new beacon %s due to empty device name", unique_id)
            return

        previously_tracked = address in self._unique_ids_by_address
        self._last_ibeacon_advertisement_by_unique_id[unique_id] = ibeacon_advertisement
        self._async_track_ibeacon_with_unique_address(address, group_id, unique_id)
        if address not in self._unavailable_trackers:
            self._unavailable_trackers[address] = bluetooth.async_track_unavailable(
                self.hass, self._async_handle_unavailable, address
            )

        if not previously_tracked and new and ibeacon_advertisement.transient:
            # Do not create a new tracker right away for transient devices
            # If they keep advertising, we will create entities for them
            # once _async_update_rssi_and_transients has seen them enough times
            self._transient_seen_count[address] = 1
            return

        # Some manufacturers violate the spec and flood us with random
        # data (sometimes its temperature data).
        #
        # Once we see more than MAX_IDS from the same
        # address we remove all the trackers for that address and add the
        # address to the ignore list since we know its garbage data.
        if len(self._group_ids_by_address[address]) >= MAX_IDS:
            self._async_ignore_address(address)
            return

        # Once we see more than MAX_IDS from the same
        # group_id we remove all the trackers for that group_id
        # as it means the addresses are being rotated.
        if len(self._addresses_by_group_id[group_id]) >= MAX_IDS:
            self._async_convert_random_mac_tracking(
                group_id, service_info, ibeacon_advertisement
            )
            return

        _async_dispatch_update(
            self.hass, unique_id, service_info, ibeacon_advertisement, new, True
        )
async def _async_update_beolink(self) -> None:
        """Update the current Beolink leader, listeners, peers and self.

        Updates Home Assistant state.
        """

        self._beolink_attributes = {}

        assert self.device_entry is not None
        assert self.device_entry.name is not None

        # Add Beolink self
        self._beolink_attributes = {
            BeoAttribute.BEOLINK: {
                BeoAttribute.BEOLINK_SELF: {self.device_entry.name: self._beolink_jid}
            }
        }

        # Add Beolink peers
        peers = await self._client.get_beolink_peers()

        if len(peers) > 0:
            self._beolink_attributes[BeoAttribute.BEOLINK][
                BeoAttribute.BEOLINK_PEERS
            ] = {}
            for peer in peers:
                self._beolink_attributes[BeoAttribute.BEOLINK][
                    BeoAttribute.BEOLINK_PEERS
                ][peer.friendly_name] = peer.jid

        # Add Beolink listeners / leader
        self._remote_leader = self._playback_metadata.remote_leader

        # Create group members list
        group_members = []

        # If the device is a listener.
        if self._remote_leader is not None:
            # Add leader if available in Home Assistant
            leader = self._get_entity_id_from_jid(self._remote_leader.jid)
            group_members.append(
                leader
                if leader is not None
                else f"leader_not_in_hass-{self._remote_leader.friendly_name}"
            )

            # Add self
            group_members.append(self.entity_id)

            self._beolink_attributes[BeoAttribute.BEOLINK][
                BeoAttribute.BEOLINK_LEADER
            ] = {
                self._remote_leader.friendly_name: self._remote_leader.jid,
            }

        # If not listener, check if leader.
        else:
            beolink_listeners = await self._client.get_beolink_listeners()
            beolink_listeners_attribute = {}

            # Check if the device is a leader.
            if len(beolink_listeners) > 0:
                # Add self
                group_members.append(self.entity_id)

                # Get the entity_ids of the listeners if available in Home Assistant
                group_members.extend(
                    [
                        listener
                        if (
                            listener := self._get_entity_id_from_jid(
                                beolink_listener.jid
                            )
                        )
                        is not None
                        else f"listener_not_in_hass-{beolink_listener.jid}"
                        for beolink_listener in beolink_listeners
                    ]
                )
                # Update Beolink attributes
                for beolink_listener in beolink_listeners:
                    for peer in peers:
                        if peer.jid == beolink_listener.jid:
                            # Get the friendly names for the listeners from the peers
                            beolink_listeners_attribute[peer.friendly_name] = (
                                beolink_listener.jid
                            )
                            break
                self._beolink_attributes[BeoAttribute.BEOLINK][
                    BeoAttribute.BEOLINK_LISTENERS
                ] = beolink_listeners_attribute

        self._attr_group_members = group_members

        self.async_write_ha_state()
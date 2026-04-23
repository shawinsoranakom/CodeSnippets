def join_players(self, group_members: list[str]) -> None:
        """Join `group_members` as a player group with the current player."""

        zone_data = self._server.roonapi.zone_by_output_id(self._output_id)
        if zone_data is None:
            _LOGGER.error("No zone data for %s", self.name)
            return

        sync_available = {}
        for zone in self._server.zones.values():
            for output in zone["outputs"]:
                if (
                    zone["display_name"] != self.name
                    and output["output_id"]
                    in self.player_data["can_group_with_output_ids"]
                    and zone["display_name"] not in sync_available
                ):
                    sync_available[zone["display_name"]] = output["output_id"]

        names = []
        for entity_id in group_members:
            name = self._server.roon_name(entity_id)
            if name is None:
                _LOGGER.error("No roon player found for %s", entity_id)
                return
            if name not in sync_available:
                _LOGGER.error(
                    (
                        "Can't join player %s with %s because it's not in the join"
                        " available list %s"
                    ),
                    name,
                    self.name,
                    list(sync_available),
                )
                return
            names.append(name)

        _LOGGER.debug("Joining %s to %s", names, self.name)
        self._server.roonapi.group_outputs(
            [self._output_id] + [sync_available[name] for name in names]
        )
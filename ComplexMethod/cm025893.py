def extra_state_attributes(self) -> dict[str, str | int | datetime]:
        """Return the state attributes of the sensor."""
        if self.entity_description.key not in self.coordinator.data:
            return {}
        player = self.coordinator.data[self.entity_description.key]

        attrs: dict[str, str | int | datetime] = {}
        if game := player.get("gameextrainfo"):
            attrs["game"] = game
        if game_id := player.get("gameid"):
            attrs["game_id"] = game_id
            game_url = f"{STEAM_API_URL}{player['gameid']}/"
            attrs["game_image_header"] = f"{game_url}{STEAM_HEADER_IMAGE_FILE}"
            attrs["game_image_main"] = f"{game_url}{STEAM_MAIN_IMAGE_FILE}"
            if info := self._get_game_icon(player):
                attrs["game_icon"] = f"{STEAM_ICON_URL}{game_id}/{info}.jpg"
        self._attr_name = str(player["personaname"]) or None
        self._attr_entity_picture = str(player["avatarmedium"]) or None
        if last_online := cast(int | None, player.get("lastlogoff")):
            attrs["last_online"] = utc_from_timestamp(mktime(localtime(last_online)))
        if level := self.coordinator.data[self.entity_description.key]["level"]:
            attrs["level"] = level
        return attrs
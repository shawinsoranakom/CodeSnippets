def _update(self) -> dict[str, dict[str, str | int]]:
        """Fetch data from API endpoint."""
        accounts = self.config_entry.options[CONF_ACCOUNTS]
        _ids = list(accounts)
        if not self.user_interface or not self.player_interface:
            self.user_interface = steam.api.interface("ISteamUser")
            self.player_interface = steam.api.interface("IPlayerService")
        if not self.game_icons:
            for _id in _ids:
                res = self.player_interface.GetOwnedGames(
                    steamid=_id, include_appinfo=1
                )["response"]
                self.game_icons = self.game_icons | {
                    game["appid"]: game["img_icon_url"] for game in res.get("games", [])
                }
        response = self.user_interface.GetPlayerSummaries(steamids=_ids)
        players = {
            player["steamid"]: player
            for player in response["response"]["players"]["player"]
            if player["steamid"] in _ids
        }
        for value in players.values():
            data = self.player_interface.GetSteamLevel(steamid=value["steamid"])
            value["level"] = data["response"].get("player_level")
        return players
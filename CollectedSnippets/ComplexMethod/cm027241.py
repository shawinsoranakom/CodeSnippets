async def async_init(self, player: Player, browse_limit: int) -> None:
        """Initialize known apps and radios from the player."""

        cmd = ["apps", 0, browse_limit]
        result = await player.async_query(*cmd)
        if result and result.get("appss_loop"):
            for app in result["appss_loop"]:
                app_cmd = "app-" + app["cmd"]
                if app_cmd not in self.known_apps_radios:
                    self.add_new_command(app_cmd, "item_id")
                    _LOGGER.debug(
                        "Adding new command %s to browse data for player %s",
                        app_cmd,
                        player.player_id,
                    )
        cmd = ["radios", 0, browse_limit]
        result = await player.async_query(*cmd)
        if result and result.get("radioss_loop"):
            for app in result["radioss_loop"]:
                app_cmd = "app-" + app["cmd"]
                if app_cmd not in self.known_apps_radios:
                    self.add_new_command(app_cmd, "item_id")
                    _LOGGER.debug(
                        "Adding new command %s to browse data for player %s",
                        app_cmd,
                        player.player_id,
                    )
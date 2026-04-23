def handle_player_config_updated(event: MassEvent) -> None:
        """Handle Mass Player Config Updated event."""
        if event.object_id is None or not event.data:
            return
        player_id = event.object_id
        player_config = PlayerConfig.from_dict(event.data)
        expose_to_ha = player_config.get_value(ATTR_CONF_EXPOSE_PLAYER_TO_HA, True)
        if not expose_to_ha and player_id in entry.runtime_data.discovered_players:
            # player is no longer exposed to Home Assistant
            remove_player(player_id)
        elif expose_to_ha and player_id not in entry.runtime_data.discovered_players:
            # player is now exposed to Home Assistant
            if not (player := mass.players.get(player_id)):
                return  # guard
            add_player(player)